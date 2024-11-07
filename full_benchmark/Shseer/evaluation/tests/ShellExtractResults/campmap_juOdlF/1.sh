#!/bin/sh

INFILE=$1.svg
OUTFILE=$1.color.svg
COLOR=$2

sed "s/#181716/#$COLOR/g" <$INFILE >$OUTFILE
