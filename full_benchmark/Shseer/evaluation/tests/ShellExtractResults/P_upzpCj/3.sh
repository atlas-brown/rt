#!/bin/sh

OUTDIR="./parts_tmp"
XSLT="template.xsl"

mkdir -p "$OUTDIR"
mkdir -p "$OUTDIR/images"

xsltproc --output "$OUTDIR/docbook.html" "$XSLT" source.xml

cp -f ../../logo/logo.png "$OUTDIR/images"
