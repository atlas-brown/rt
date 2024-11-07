#!/usr/bin/env bash
#
# Copyright 2010-2018 OpenEstate.org
#

URL="https://github.com/OpenEstate/OpenEstate-PHP-Export/archive/develop-1.7.tar.gz"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TEMP_DIR="$DIR/temp"
PHPEXPORT_DIR="$DIR/phpexport"
set -e

echo ""
echo "Downloading development version of PHP-Export 1.7..."
mkdir -p "$TEMP_DIR"
rm -Rf "$TEMP_DIR/phpexport.tar.gz"
curl -L \
  -o "$TEMP_DIR/phpexport.tar.gz" \
  "$URL"
if [ ! -f "$TEMP_DIR/phpexport.tar.gz" ]; then
    echo "ERROR: PHP-Export was not properly downloaded!"
    exit 1
fi

echo ""
echo "Extracting PHP-Export..."
rm -Rf "$PHPEXPORT_DIR"
rm -Rf "$TEMP_DIR/phpexport"
mkdir -p "$TEMP_DIR/phpexport"
cd "$TEMP_DIR/phpexport"
tar xfz "$TEMP_DIR/phpexport.tar.gz"
mv "$(ls -1)/src" "$PHPEXPORT_DIR"
rm -Rf "$TEMP_DIR/phpexport"

echo ""
echo "PHP-Export was successfully extracted!"
echo "to: $PHPEXPORT_DIR"
