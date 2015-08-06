#!/bin/bash

while read -r url; do
    echo "$url"
    curl -O "$url"
    if [[ -f *.sucatalog.gz ]]; then
        gunzip -f *.sucatalog.gz
    fi
done < <(strings /System/Library/PrivateFrameworks/SoftwareUpdate.framework/SoftwareUpdate | grep '^http' | grep sucatalog)
