#!/bin/sh
#desc:Edit file
#package:oddevel

# Copyright(c) 2015 OpenDomo Services SL. Licensed under GPL v3 or later

extension=${1##*.}
TMPDIR="/var/opendomo/tmp"

if ! test -z "$3"; then
	bname=`basename $1`
	cp $TMPDIR/$bname $TMPDIR/$1
fi

echo "#>Editing file"
echo "form:editFile.sh"
echo "	fullpath	Filename	hidden	$1"
case $extension in
	jpeg|jpg|png|gif)
		bname=`basename $1`
		cp $TMPDIR/$1 $TMPDIR/$bname
		echo "	fullpath	fullpath	hidden	$1"
		echo "	filecontent	File contents 	application	/cgi-bin/displayfile.cgi?$1"
		echo "	realfile	Upload file	file	$bname"
		echo "actions:"
		echo "	goback	Back"
		echo "	editFile.sh	Save changes"
		;;
	*)
		echo "	filecontent	File contents 	application	/cgi-bin/texteditor.py?fname=$1"
		echo "actions:"
		echo
		;;
esac
echo 