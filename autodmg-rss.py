#!/usr/bin/python
#
#-*- coding: utf-8 -*-


import sys
import argparse
import urllib2
from xml.etree import ElementTree
import re


FEED_URL = u"http://rss.support.apple.com/?channel=DOWNLOADS"


def printf8(f, *args):
    print >>f, " ".join(unicode(x).encode(u"utf-8") for x in args)


re_url = re.compile(ur"download_link.setAttribute\('href',\s*'(?P<url>.+\.dmg)'\)")

def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument(u"-v", u"--verbose", action=u"store_true",
                   help=u"Verbose output.")
    p.add_argument(u"updates", help=u"plist with updates")
    args = p.parse_args(argv[1:])
    
    if args.verbose:
        print >>sys.stderr, u"Downloading %s" % FEED_URL
    try:
        f = urllib2.urlopen(FEED_URL)
        feed = ElementTree.parse(f)
    except urllib2.URLError as e:
        sys.exit(u"Feed fetching failed: %s" % unicode(e))
    except ElementTree.ParseError as e:
        sys.exit(u"Feed parsing failed: %s" % unicode(e))
    
    with open(args.updates, "w") as f:
        printf8(f, u'<?xml version="1.0" encoding="UTF-8"?>')
        printf8(f, u'<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">')
        printf8(f, u'<plist version="1.0">')
        printf8(f, u'<dict>')
        printf8(f, u'\t<key>Updates</key>')
        printf8(f, u'\t<dict>')
        root = feed.getroot()
        for item in root.findall(u"channel/item"):
            name = item.find(u"title").text
            if name.startswith(u"iOS") or name.startswith(u"iTunes") or u"Windows" in name:
                continue
            kb_url = item.find(u"link").text
            if args.verbose:
                print u"Downloading %s" % kb_url
            try:
                html = urllib2.urlopen(kb_url).read()
            except urllib2.URLError as e:
                sys.exit(u"Feed fetching failed: %s" % unicode(e))
            m = re_url.search(html)
            if m:
                url = m.group(u"url")
                if url.startswith(u"/downloads"):
                    url = u"http://support.apple.com" + url
                printf8(f, u"\t\t<key></key>")
                printf8(f, u"\t\t<dict>")
                printf8(f, u"\t\t\t<key>name</key>")
                printf8(f, u"\t\t\t<string>%s</string>" % name)
                printf8(f, u"\t\t\t<key>url</key>")
                printf8(f, u"\t\t\t<string>%s</string>" % url)
                printf8(f, u"\t\t</dict>")
            else:
                print >>sys.stderr, u"No download button found for %s" % name
        
        printf8(f, u'\t</dict>')
        printf8(f, u'</dict>')
        printf8(f, u'</plist>')
    
    return 0
    

if __name__ == '__main__':
    sys.exit(main(sys.argv))
    
