#!/bin/sh
if [ $# -gt 2 ] ; then
	echo "Expected at most 2 arguments"
	exit 1
fi
while getopts "d" n
do
  case "$n" in
    d) delold="y" ;;
    *) true ;;
  esac
done
shift $((OPTIND))
install_dir="$1"

cd "$install_dir" || exit 1

if [ "$delold" = "y" ] ; then
	rm -fr ./*
fi
