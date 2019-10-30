#!/usr/bin/python
# -*- coding: utf-8 -*-


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


import os
import argparse
import plistlib
import datetime
import re
import urllib2


re_build = re.compile(ur'^(?P<major>\d+)(?P<minor>[A-Z])(?P<build>.+)$')

def verify_verbuild(verbuild):
    ver, _, build = verbuild.partition("-")
    vers = list(int(x) for x in ver.split("."))
    if len(vers) not in [2, 3]:
        print("ERROR: Bad version: %s" % verbuild)
        return False
    if vers[0] != 10:
        print("ERROR: Bad version: %s" % verbuild)
        return False
    major = vers[1]
    try:
        minor = vers[2]
    except IndexError:
        minor = 0
    if (major < 7) or (major > 16):
        print("ERROR: Bad version: %s" % verbuild)
        return False
    if (minor < 0) or (minor > 15):
        print("ERROR: Bad version: %s" % verbuild)
        return False
    m = re_build.search(build)
    if not m:
        print("ERROR: Bad build: %s" % verbuild)
        return False
    build_major = int(m.group("major"))
    build_minor = ord(m.group("minor")) - 0x41
    if build_major != major + 4:
        print("ERROR: build major does not match OS major: %s" % verbuild)
        return False
    if build_minor != minor:
        print("ERROR: build minor does not match OS minor: %s" % verbuild)
        return False
    return True


def get_http_code(url):
    try:
        f = urllib2.urlopen(url)
    except urllib2.HTTPError as e:
        return e.code
    except urllib2.URLError as e:
        print("%s failed with error %s" % (url, e))
        return -1
    f.close()
    return f.getcode()


def main(argv):
    p = argparse.ArgumentParser()
    p.add_argument("-v", "--verbose", action="store_true",
                   help="Verbose output.")
    p.add_argument("updates", default="UpdateProfiles.plist", nargs="?", help="plist with updates")
    args = p.parse_args([x.decode("utf-8") for x in argv[1:]])
    
    try:
        plist = plistlib.readPlist(args.updates)
    except BaseException as e:
        sys.exit("Couldn't read plist: %s" % unicode(e))
    
    error_count = 0
    
    # Verify root keys.
    expected_keys = set(["DeprecatedInstallers", "DeprecatedOSVersions", "PublicationDate", "Profiles", "Updates"])
    found_keys = set(plist.iterkeys())
    if found_keys != expected_keys:
        missing_keys = expected_keys - found_keys
        unexpected_keys = found_keys - expected_keys
        if missing_keys:
            sys.exit("Error: Missing keys in plist: %s" % ", ".join(missing_keys))
        else:
            sys.exit("Error: Unexpected keys in plist: %s" % ", ".join(unexpected_keys))
    
    # Verify DeprecatedInstallers.
    supported_builds = set(x.partition("-")[2] for x in plist["DeprecatedInstallers"].iterkeys())
    re_osbuild = re.compile(ur'^\d+[A-Z]\d+[a-z]?$')
    for replacement, replaced in plist["DeprecatedInstallers"].iteritems():
        if not verify_verbuild(replacement):
            error_count += 1
        for build in replaced:
            if not re_osbuild.search(build):
                print("Error: invalid deprecated build %s" % build)
                error_count += 1
            if build in supported_builds:
                print("Error: %s deprecates supported build %s" % (replacement, build))
                error_count += 1
    
    # Verify PublicationDate.
    age = datetime.datetime.utcnow() - plist["PublicationDate"]
    if age.seconds > 300:
        print("Warning: PublicationDate is %s" % plist["PublicationDate"])
    
    # Verify Profiles.
    known_updates = set(plist["Updates"].iterkeys())
    referenced_updates = set()
    for profile, updates in plist["Profiles"].iteritems():
        if not verify_verbuild(profile):
            error_count += 1
        for update in updates:
            if not update in known_updates:
                print("Error: Profile %s references unknown update: %s" % (profile, update))
                error_count += 1
            else:
                referenced_updates.add(update)
    if referenced_updates != known_updates:
        unreferenced_updates = known_updates - referenced_updates
        if unreferenced_updates:
            print("Error: Unreferenced updates: %s" % ", ".join(unreferenced_updates))
            error_count += 1
    
    # Verify Updates.
    for update, info in plist["Updates"].iteritems():
        expected_keys = set(["name", "sha1", "size", "url"])
        found_keys = set(info.iterkeys())
        if found_keys != expected_keys:
            missing_keys = expected_keys - found_keys
            unexpected_keys = found_keys - expected_keys
            if missing_keys:
                print("Error: Update %s is missing keys: %s" % (update, ", ".join(missing_keys)))
                error_count += 1
            else:
                print("Error: Update %s has unknown keys: %s" % (update, ", ".join(unexpected_keys)))
                error_count += 1
        code = get_http_code(info["url"])
        if code != 200:
            print("Error: Update %s returns HTTP error %d" % (update, code))
            error_count += 1

    if error_count:
        return os.EX_DATAERR
    else:
        print("Verified profiles:")
        for verbuild in sorted(plist["Profiles"].iterkeys()):
            deprecated = False
            for depver in plist["DeprecatedOSVersions"]:
                splitver = depver.split(".")
                if splitver == verbuild.split(".")[:len(splitver)]:
                    deprecated = True
            print("  %s%s" % (verbuild, " (deprecated)" if deprecated else ""))
        return os.EX_OK
    

if __name__ == '__main__':
    sys.exit(main(sys.argv))
    
