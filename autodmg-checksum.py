#!/usr/bin/python
#
#-*- coding: utf-8 -*-


import sys
import argparse
import urllib2
import hashlib
import plistlib
import os
import datetime


UPDATE_DIR = os.path.expanduser(u"~/Library/Application Support/AutoDMG/Updates")

def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument(u"-v", u"--verbose", action=u"store_true",
                   help=u"Verbose output")
    p.add_argument(u"-n", u"--nosave", action=u"store_true",
                   help=u"Don't save downloaded files to AutoDMG/Updates")
    p.add_argument(u"-f", u"--force", action=u"store_true",
                   help=u"Force checksum update")
    p.add_argument(u"updates", help=u"plist with updates")
    args = p.parse_args(argv[1:])
    
    try:
        plist = plistlib.readPlist(args.updates)
    except BaseException as e:
        sys.exit(u"Couldn't read plist: %s" % unicode(e))
    
    if not os.path.exists(UPDATE_DIR):
        try:
            os.makedirs(UPDATE_DIR)
        except OSError as e:
            sys.exit(u"Failed to create %s: %s" % (UPDATE_DIR, unicode(e)))
    
    for name, info in plist[u"Updates"].iteritems():
        print name
        if args.force or (not u"sha1" in info) or (not u"size" in info):
            f = urllib2.urlopen(info[u"url"])
            data = f.read()
            m = hashlib.sha1()
            m.update(data)
            info[u"sha1"] = m.hexdigest()
            info[u"size"] = len(data)
            with open(os.path.join(UPDATE_DIR, info[u"sha1"]), "w") as f:
                f.write(data)
        print u"    name: %s" % (info[u"name"])
        print u"    url: %s" % (info[u"url"])
        print u"    sha1: %s" % (info[u"sha1"])
        print u"    size: %d" % (info[u"size"])
        print u""
    
    plist[u"PublicationDate"] = datetime.datetime.utcnow()
    plistlib.writePlist(plist, args.updates)
    
    return 0
    

if __name__ == '__main__':
    sys.exit(main(sys.argv))
    
