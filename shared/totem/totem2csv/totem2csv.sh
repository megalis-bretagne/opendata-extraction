#!/bin/bash

if [ "$1" == "" ]; then
    cmd=`basename $0`
    echo "usage: $cmd $0 <totemxmlfile>"
    exit 1
fi
totemfile=$1

if [ ! -e $totemfile ]; then
    echo "totem file [$totemfile] not found"
    exit 1
fi

output_prefix=`basename -s .xml $totemfile`

echo "Converting totem file $totemfile"
python3 shared/totem/totem2csv/xmlcsv2csv.py "$totemfile" "$output_prefix"
echo "Conversion finished."
