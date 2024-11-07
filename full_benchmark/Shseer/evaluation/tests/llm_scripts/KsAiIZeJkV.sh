#!/bin/sh

if [ -f $1 ] ; then
    pdfto$2 $1 $3
fi
