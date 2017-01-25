#!/usr/bin/python
# -*- coding: utf-8 -*-


"""Helper tool to generate AutoDMG profiles."""


from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
import io
import sys
import codecs
if sys.stdout.encoding != "UTF-8":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout, "strict")
if sys.stderr.encoding != "UTF-8":
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr, "strict")


from xml.etree import ElementTree
import argparse
import re
import urllib2
import plistlib


FEED_URL = "http://rss.support.apple.com/?channel=DOWNLOADS"

INCLUDED_UPDATES = [
    "Update",
    "Safari",
    "iTunes",
]

EXCLUDED_UPDATES = [
    "Windows",
    "Firmware",
    "Combo",
]


def get_download_url(link):
    """Follows HTTP 302 redirects to fetch the final url of a download."""
    base_url = "https://support.apple.com"
    article_number = link.split("/")[-1]
    download_url = ("{}/downloads/{}/en_US/".format(base_url, article_number))
    try:
        request = urllib2.Request(download_url)
        response = urllib2.urlopen(request)
    except BaseException as e:
        sys.exit("Can't download %s: %s" % (download_url, unicode(e)))
    
    filename = response.geturl().split("/")[-1]
    return "{}{}".format(download_url, filename)


def get_itunes_download_url(title):
    """Takes the title of an iTunes update and attempts to find a suitble
    download link from the iTunes download page.
    """
    re_version = re.compile(ur"(?P<version>(?:(\d+)\.)?(?:(\d+)\.)?(\d+)(.*))")
    itunes_base_url = "https://swdlp.apple.com/iframes/82/en_us/82_en_us.html"
    
    # Figure out which version we need a url for
    version_match = re_version.search(title)
    if version_match:
        version = version_match.group("version")
    
    # Build a regex to include the version number
    re_url = re.compile(ur"value='(https://.*?iTunes{}.dmg)'".format(version))
    
    try:
        html = urllib2.urlopen(itunes_base_url).read()
    except urllib2.URLError as e:
        sys.exit("Feed fetching failed: %s" % unicode(e))
    
    url_match = re_url.search(html)
    if url_match:
        return url_match.group(1)


def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument("-v", "--verbose", action="store_true",
                   help="Verbose output.")
    p.add_argument("updates", help="plist with updates")
    args = p.parse_args(argv[1:])
    
    if args.verbose:
        print("Downloading {}\n".format(FEED_URL))
    
    try:
        rss_feed = urllib2.urlopen(FEED_URL)
        rss_feed = ElementTree.parse(rss_feed)
    except urllib2.URLError as e:
        sys.exit("Feed fetching failed: %s" % unicode(e))
    except ElementTree.ParseError as e:
        sys.exit("Feed parsing failed: %s" % unicode(e))
    
    updates_found = {"Updates": {}}
    
    for item in rss_feed.findall(".//item"):
        title = item.find("title").text
        if title.startswith("Download "):
            title = title[9:]
        
        # Only includes updates with "INCLUDED_UPDATES" in the title.
        # Filters out "EXCLUDED_UPDATES" for things we don't care about.
        if (not any(update in title for update in INCLUDED_UPDATES) or
                any(update in title for update in EXCLUDED_UPDATES)):
            if args.verbose:
                print("Skipping {}\n".format(title))
            continue
        
        link = item.find("link").text
        if not link:
            print("Unable to find link for {}".format(title))
            continue
        url = get_download_url(link)
        if not url:
            print("Unable to find URL for {}".format(title))
            continue
        
        if (".dmg" or ".pkg") not in url:
            if "iTunes" in title:
                url = get_itunes_download_url(title)
        
        print("# {}".format(title))
        if args.verbose:
            print(url + "\n")
        
        update = {
            "name": title,
            "url": url,
        }
        
        updates_found["Updates"][link.split("/")[-1]] = update
    
    print("Saving to {}".format(args.updates))
    plistlib.writePlist(updates_found, args.updates)
    
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
