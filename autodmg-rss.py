#!/usr/bin/python
# -*- coding: utf-8 -*-


"""Helper tool to generate AutoDMG profiles."""


from xml.etree import ElementTree
import sys
import argparse
import re
import urllib2
import plistlib


FEED_URL = u"http://rss.support.apple.com/?channel=DOWNLOADS"

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


def print8(*args):
    print " ".join(unicode(x).encode(u"utf-8") for x in args)

def printerr8(*args):
    print >>sys.stderr, " ".join(unicode(x).encode(u"utf-8") for x in args)


def get_download_url(link):
    """Follows HTTP 302 redirects to fetch the final url of a download."""
    base_url = u"https://support.apple.com"
    article_number = link.split("/")[-1]
    download_url = (u"{}/downloads/{}/en_US/".format(base_url, article_number))
    try:
        request = urllib2.Request(download_url)
        response = urllib2.urlopen(request)
    except BaseException as e:
        sys.exit(u"Can't download %s: %s" % (download_url, unicode(e)))
    
    filename = response.geturl().split(u"/")[-1]
    return u"{}{}".format(download_url, filename)


def get_itunes_download_url(title):
    """Takes the title of an iTunes update and attempts to find a suitble
    download link from the iTunes download page.
    """
    re_version = re.compile(ur"(?P<version>(?:(\d+)\.)?(?:(\d+)\.)?(\d+)(.*))")
    itunes_base_url = u"https://swdlp.apple.com/iframes/82/en_us/82_en_us.html"
    
    # Figure out which version we need a url for
    version_match = re_version.search(title)
    if version_match:
        version = version_match.group(u"version")
    
    # Build a regex to include the version number
    re_url = re.compile(ur"value='(https://.*?iTunes{}.dmg)'".format(version))
    
    try:
        html = urllib2.urlopen(itunes_base_url).read()
    except urllib2.URLError as e:
        sys.exit(u"Feed fetching failed: %s" % unicode(e))
    
    url_match = re_url.search(html)
    if url_match:
        return url_match.group(1)


def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument(u"-v", u"--verbose", action=u"store_true",
                   help=u"Verbose output.")
    p.add_argument(u"updates", help=u"plist with updates")
    args = p.parse_args(argv[1:])
    
    if args.verbose:
        printerr8(u"Downloading %s\n" % FEED_URL)
    
    try:
        rss_feed = urllib2.urlopen(FEED_URL)
        rss_feed = ElementTree.parse(rss_feed)
    except urllib2.URLError as e:
        sys.exit(u"Feed fetching failed: %s" % unicode(e))
    except ElementTree.ParseError as e:
        sys.exit(u"Feed parsing failed: %s" % unicode(e))
    
    updates_found = {u"Updates": {}}
    
    for item in rss_feed.findall(u".//item"):
        title = item.find(u"title").text
        # Only includes updates with "INCLUDED_UPDATES" in the title.
        # Filters out "EXCLUDED_UPDATES" for things we don't care about.
        if (not any(update in title for update in INCLUDED_UPDATES) or
                any(update in title for update in EXCLUDED_UPDATES)):
            if args.verbose:
                print8(u"Skipping {}\n".format(title))
            continue
        
        link = item.find(u"link").text
        url = get_download_url(link)
        
        if (u".dmg" or u".pkg") not in url:
            if u"iTunes" in title:
                url = get_itunes_download_url(title)
        
        print8(title)
        if args.verbose:
            print8(url + u"\n")
        
        update = {
            u"name": title,
            u"url": url,
        }
        
        updates_found[u"Updates"][link.split(u"/")[-1]] = update
    
    plistlib.writePlist(updates_found, args.updates)
    
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
