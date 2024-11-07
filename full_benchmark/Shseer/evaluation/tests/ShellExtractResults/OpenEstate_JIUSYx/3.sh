#!/usr/bin/env bash
#
# Copyright 2010-2018 OpenEstate.org
#

XGETTEXT="xgettext"
NAME="openestate-php-wrapper"
VERSION="0.3.0"
AUTHOR_NAME="OpenEstate.org"
AUTHOR_EMAIL="info@openestate.org"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo "creating \"$NAME.pot\""
cd "$DIR/src"
"$XGETTEXT" \
  --default-domain="$NAME" \
  --language="PHP" \
  --keyword="__" \
  --keyword="_e" \
  --sort-by-file \
  --from-code="UTF-8" \
  --copyright-holder="$AUTHOR_NAME" \
  --package-name="$NAME" \
  --package-version="$VERSION" \
  --msgid-bugs-address="$AUTHOR_EMAIL" \
  --output="$DIR/src/languages/$NAME.pot" \
  *.php
