#!/usr/bin/python
#
#-*- coding: utf-8 -*-


import sys
import argparse
import urllib2
from xml.etree import ElementTree
import re


FEED_URL = u"http://rss.support.apple.com/?channel=DOWNLOADS"


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
        print >>f, u'<?xml version="1.0" encoding="UTF-8"?>'
        print >>f, u'<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
        print >>f, u'<plist version="1.0">'
        print >>f, u'<dict>'
        print >>f, u'\t<key>Updates</key>'
        print >>f, u'\t<dict>'
        root = feed.getroot()
        for item in root.findall(u"channel/item"):
            name = item.find(u"title").text
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
                print >>f, u"\t\t<key></key>"
                print >>f, u"\t\t<dict>"
                print >>f, u"\t\t\t<key>name</key>"
                print >>f, u"\t\t\t<string>%s</string>" % name
                print >>f, u"\t\t\t<key>url</key>"
                print >>f, u"\t\t\t<string>%s</string>" % url
                print >>f, u"\t\t</dict>"
            else:
                print >>sys.stderr, u"No download button found for %s" % name
        
        print >>f, u'\t</dict>'
        print >>f, u'</dict>'
        print >>f, u'</plist>'
    
    return 0
    

if __name__ == '__main__':
    sys.exit(main(sys.argv))
    
