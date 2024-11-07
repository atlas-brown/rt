#!/usr/bin/env bash
#
# Copyright 2010-2018 OpenEstate.org
#

URL="https://wordpress.org/latest.tar.gz"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
TEMP_DIR="$DIR/temp"
WORDPRESS_DIR="$DIR/wordpress"
set -e

echo ""
echo "Downloading latest version of WordPress..."
mkdir -p "$TEMP_DIR"
rm -Rf "$TEMP_DIR/wordpress.tar.gz"
curl -L \
  -o "$TEMP_DIR/wordpress.tar.gz" \
  "$URL"
if [ ! -f "$TEMP_DIR/wordpress.tar.gz" ]; then
    echo "ERROR: WordPress was not properly downloaded!"
    exit 1
fi

echo ""
echo "Extracting WordPress..."
rm -Rf "$WORDPRESS_DIR"
rm -Rf "$TEMP_DIR/wordpress"
mkdir -p "$TEMP_DIR/wordpress"
cd "$TEMP_DIR/wordpress"
tar xfz "$TEMP_DIR/wordpress.tar.gz"
mv "$(ls -1)" "$WORDPRESS_DIR"
rm -Rf "$TEMP_DIR/wordpress"

echo ""
echo "WordPress was successfully extracted!"
echo "to: $WORDPRESS_DIR"
