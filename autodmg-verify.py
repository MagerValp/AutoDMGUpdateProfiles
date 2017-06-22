#!/usr/bin/python
# -*- coding: utf-8 -*-


from __future__ import print_function

import os
import sys
import argparse
import plistlib
import datetime
import re


def uprint(*args, **kwargs):
    try:
        encoding = kwargs[u"encoding"]
        del kwargs[u"encoding"]
    except KeyError:
        encoding = u"utf-8"
    
    encoded_objects = list()
    for obj in args:
        if isinstance(obj, unicode):
            encoded_objects.append(obj.encode(encoding))
        else:
            encoded_objects.append(obj)
    print(*encoded_objects, **kwargs)


def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument(u"-v", u"--verbose", action=u"store_true",
                   help=u"Verbose output.")
    p.add_argument(u"updates", help=u"plist with updates")
    args = p.parse_args([x.decode(u"utf-8") for x in argv[1:]])
    
    try:
        plist = plistlib.readPlist(args.updates)
    except BaseException as e:
        sys.exit(u"Couldn't read plist: %s" % unicode(e))
    
    error_count = 0
    
    # Verify root keys.
    expected_keys = set([u"DeprecatedInstallers", u"DeprecatedOSVersions", u"PublicationDate", u"Profiles", u"Updates"])
    found_keys = set(plist.iterkeys())
    if found_keys != expected_keys:
        missing_keys = expected_keys - found_keys
        unexpected_keys = found_keys - expected_keys
        if missing_keys:
            sys.exit(u"Error: Missing keys in plist: %s" % u", ".join(unicode(key) for key in missing_keys))
        else:
            sys.exit(u"Error: Unexpected keys in plist: %s" % u", ".join(unicode(key) for key in unexpected_keys))
    
    # Verify DeprecatedInstallers.
    supported_builds = set(x.partition(u"-")[2] for x in plist[u"DeprecatedInstallers"].iterkeys())
    re_osbuild = re.compile(ur'^\d+[A-Z]\d+[a-z]?$')
    for replacement, replaced in plist[u"DeprecatedInstallers"].iteritems():
        for build in replaced:
            if not re_osbuild.search(build):
                uprint(u"Error: invalid deprecated build %s" % build)
                error_count += 1
            if build in supported_builds:
                uprint(u"Error: %s deprecates supported build %s" % (replacement, build))
                error_count += 1
    
    # Verify PublicationDate.
    age = datetime.datetime.utcnow() - plist[u"PublicationDate"]
    if age.seconds > 300:
        uprint(u"Warning: PublicationDate is %s" % unicode(plist[u"PublicationDate"]))
    
    # Verify Profiles.
    known_updates = set(plist[u"Updates"].iterkeys())
    referenced_updates = set()
    for profile, updates in plist[u"Profiles"].iteritems():
        for update in updates:
            if not update in known_updates:
                uprint(u"Error: Profile %s references unknown update: %s" % (profile, update))
                error_count += 1
            else:
                referenced_updates.add(update)
    if referenced_updates != known_updates:
        unreferenced_updates = known_updates - referenced_updates
        if unreferenced_updates:
            uprint(u"Error: Unreferenced updates: %s" % u", ".join(unicode(key) for key in unreferenced_updates))
            error_count += 1
    
    # Verify Updates.
    for update, info in plist[u"Updates"].iteritems():
        expected_keys = set([u"name", u"sha1", u"size", u"url"])
        found_keys = set(info.iterkeys())
        if found_keys != expected_keys:
            missing_keys = expected_keys - found_keys
            unexpected_keys = found_keys - expected_keys
            if missing_keys:
                uprint(u"Error: Update %s is missing keys: %s" % (update, u", ".join(unicode(key) for key in missing_keys)))
                error_count += 1
            else:
                uprint(u"Error: Update %s has unknown keys: %s" % (update, u", ".join(unicode(key) for key in unexpected_keys)))
                error_count += 1
    
    if error_count:
        return os.EX_DATAERR
    else:
        uprint(u"Verified profiles:")
        for verbuild in sorted(plist[u"Profiles"].iterkeys()):
            deprecated = False
            for depver in plist[u"DeprecatedOSVersions"]:
                splitver = depver.split(u".")
                if splitver == verbuild.split(u".")[:len(splitver)]:
                    deprecated = True
            uprint(u"  %s%s" % (verbuild, u" (deprecated)" if deprecated else u""))
        return os.EX_OK
    

if __name__ == '__main__':
    sys.exit(main(sys.argv))
    
