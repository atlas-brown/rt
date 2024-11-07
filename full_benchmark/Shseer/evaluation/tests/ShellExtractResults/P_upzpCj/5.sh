#!/bin/sh

OUTDIR="manual"
XSLT="/usr/share/xml/docbook/stylesheet/docbook-xsl/xhtml/profile-chunk.xsl"

if [ "$1" ]; then OUTDIR=$1; fi

mkdir -p "$OUTDIR"
mkdir -p "$OUTDIR/images"

xsltproc --output "$OUTDIR/docbook.html" "$XSLT" source.xml

cp -f ../../logo/logo.png "$OUTDIR/images"
