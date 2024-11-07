#!/bin/sh
# Called from the project root by 'make man'

set -e 

VERSION=$(git describe --dirty)
TITLE='Charm Manual'
FILES=$(echo "~/.go-cookies\tHolds  authentication  tokens  for communicating with the charmstore.
~/.cache/charm-command-cache\tHolds cache for descriptions of extended core charm commands.")

dir=$(dirname $0)
$dir/generate-manpage.py -a 'https://jujucharms.com' -f "$FILES" -v "$VERSION" -t "$TITLE" charm

for cmd in $(charm help | awk '{if (x==1) {print $1} if( $1=="commands:")x=1;} ') 
do
    $dir/generate-manpage.py -a 'https://jujucharms.com' -s "$cmd" -t "$TITLE" -v "$VERSION" charm

done
