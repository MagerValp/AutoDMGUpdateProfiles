#!/bin/bash


if [[ -z "$1" ]]; then
    plist="UpdateProfiles.plist"
else
    plist="$1"
fi

if ! ./autodmg-verify.py "$plist"; then
    exit 1
fi
cp -v "$plist" ~/Library/Application\ Support/AutoDMG/
