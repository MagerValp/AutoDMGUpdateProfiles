AutoDMGUpdateProfiles
=====================


This repository contains two utilities to help generate update profiles for [AutoDMG](https://github.com/MagerValp/AutoDMG)


autodmg-rss.py
--------------

`autodmg-rss.py` reads [Apple's RSS feed for software updates](http://rss.support.apple.com/?channel=DOWNLOADS) and creates a plist with the name and URL of each update. Not all updates have standard download buttons (notably iTunes), and some updates are only available from Software Update, so some will have to be added manually.


autodmg-checksum.py
-------------------

`autodmg-checksum.py` takes the plist from `autodmg-rss.py` and downloads each update that doesn't have the sha1 checksum or size set. It also updates the PublicationDate to the current time, and it saves the updates for you in `AutoDMG/Updates`.


Suggested Workflow
==================

1. Install a bare OS on a test machine, and perform initial setup.
2. Run `sudo softwareupdate -l -a`.
3. Note the updates and the order they appear in.
4. Run `./autodmg-rss.py updates.plist`.
5. Edit updates.plist, add any updates that `autodmg-rss.py` doesn't find, and remove irrelevant updates.
6. Run `./autodmg-checksum.py updates.plist`.
7. Use `updates.plist` to update AutoDMG's `UpdateProfiles.plist`, while paying attention to installation order.
8. Move `UpdateProfiles.plist` into `~/Library/Application Support/AutoDMG` for testing.
