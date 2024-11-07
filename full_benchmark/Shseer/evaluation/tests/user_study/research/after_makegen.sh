#!/bin/bash
##
## makegen - generate a basic skeleton C project Makefile
## Copyright (C) 2020 Daniel Haase
##
## This program is free software: you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program. If not, see <http://www.gnu.org/licenses/gpl.txt>.
##

function checkcmd
{
	local c="$1"
	if [ $# -eq 0 ] || [ -z "$c" ]; then return 0; fi
	which "$c" &> /dev/null
	if [ $? -ne 0 ]; then echo "command \"$c\" not found"; exit 2; fi
	return 0
}

## "make" is not a dependency but generating a Makefile for a system
## not having the "make" utility installed makes little sense
checkcmd "make"

## check dependencies
checkcmd "basename"
checkcmd "mkdir"
checkcmd "touch"

if [ $# -eq 2 ]; then
	PROJECT="$1"
	LOCATION="$2"
elif [ $# -eq 1 ]; then
	if [ "$1" == "--help" ]; then
		echo "usage:  $(basename $0) <project> [<location>]"
		exit 0
	elif [ -d "./$1" ]; then
		PROJECT="$1"
		LOCATION="./$1"
	else
		PROJECT="$1"
		LOCATION="."
	fi
else
	echo "usage:  $(basename $0) <project> [<location>]"
	exit 1
fi

mkdir -p "$LOCATION" &> /dev/null
mkdir -p "$LOCATION/src" &> /dev/null
mkdir -p "$LOCATION/obj" &> /dev/null
mkdir -p "$LOCATION/bin" &> /dev/null
MKFILE="$LOCATION/Makefile"
SRCFILE="$LOCATION/src/$PROJECT.c"

touch $MKFILE
echo "OUT = $PROJECT" >> $MKFILE
echo "CC = gcc" >> $MKFILE
echo "ED = zile" >> $MKFILE
echo "CSTD = -std=gnu99" >> $MKFILE
echo "INCS = " >> $MKFILE
echo "DEFS = -DDEBUG -DLINUX" >> $MKFILE
echo "TARG = \$(CSTD) -m64" >> $MKFILE
echo "WARN = -Wall -Werror -Wextra -Wunused -Wstrict-prototypes -pedantic -pedantic-errors" >> $MKFILE
echo "CFLAGS = \$(TARG) \$(WARN) \$(INCS) \$(DEFS)" >> $MKFILE
echo "LDFLAGS = " >> $MKFILE
echo "objects = " >> $MKFILE
echo "" >> $MKFILE
echo ".PHONY: all clean edit run pack" >> $MKFILE
echo "" >> $MKFILE
echo "all: \$(OUT)" >> $MKFILE
echo "" >> $MKFILE
echo "\$(OUT): obj/\$(OUT).o \$(objects)" >> $MKFILE
echo "	\$(CC) -o bin/\$(OUT) \$(LDFLAGS) \$^" >> $MKFILE
echo "" >> $MKFILE
echo "obj/\$(OUT).o: src/\$(OUT).c" >> $MKFILE
echo "	\$(CC) -c \$(CFLAGS) -o \$@ \$<" >> $MKFILE
echo "" >> $MKFILE
echo "clean:" >> $MKFILE
echo "	rm -f bin/\$(OUT) obj/*.o src/*~ core.*" >> $MKFILE
echo "" >> $MKFILE
echo "pack:" >> $MKFILE
echo "	tar cJf ${PROJECT}.txz Makefile src/" >> $MKFILE
echo "" >> $MKFILE
echo "edit:" >> $MKFILE
echo "	\$(ED) src/\$(OUT).c" >> $MKFILE
echo "" >> $MKFILE
echo "run: \$(OUT)" >> $MKFILE
echo "	./bin/\$(OUT)" >> $MKFILE
echo "" >> $MKFILE

touch $SRCFILE
echo "#include <stdio.h>" >> $SRCFILE
echo "" >> $SRCFILE
echo "int main(void)" >> $SRCFILE
echo "{" >> $SRCFILE
echo "	return 0;" >> $SRCFILE
echo "}" >> $SRCFILE
echo "" >> $SRCFILE

echo "done"
exit 0
