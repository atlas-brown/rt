#!/usr/bin/env bash
#
# Copyright 2010-2018 OpenEstate.org
#

MSGFMT="msgfmt"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LANGUAGES_DIR="$DIR/src/languages"

for f in "$LANGUAGES_DIR"/*.po
do
  name="$(basename -s .po $f)"
  echo "compiling \"$name.po\" to \"$name.mo\""
  "$MSGFMT" --output-file="$LANGUAGES_DIR/$name.mo" "$LANGUAGES_DIR/$name.po"
done
