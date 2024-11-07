#!/bin/bash

APXS_BIN=$1

echo "Installing apache module..."

if type "chrpath" > /dev/null; then
	echo " - Removing hardcoded rpath"
	chrpath -d .libs/libmod_pstar.so
fi

if test ! -L mod_pstar.so ; then ln -s .libs/libmod_pstar.so mod_pstar.so ; fi

if [ "$APXS_DH_CONTEXT" == "1" ]; then
	echo " - Hard-copy into debian directory"
	cp mod_pstar.so ../../debian/libapache2-mod-pstar/usr/lib/apache2/modules/mod_pstar.so
else
	echo " - Using $APXS_BIN"
	$APXS_BIN -i -n mod_pstar mod_pstar.so
	echo $?
fi

