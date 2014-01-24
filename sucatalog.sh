#!/bin/bash

while read -r url; do
    echo "$url"
    curl -O "$url"
done < <(strings /System/Library/PrivateFrameworks/SoftwareUpdate.framework/SoftwareUpdate | grep '^http' | grep sucatalog)
