#!/bin/bash

rm -f *.sucatalog *.sucatalog.gz
while read -r url; do
    echo "$url"
    curl -O "$url"
    gunzip -f *.sucatalog.gz 2>/dev/null
done < <(strings /System/Library/PrivateFrameworks/SoftwareUpdate.framework/SoftwareUpdate | grep '^http' | grep sucatalog)
