#!/bin/bash

if [ $# -eq 2 ]; then
	PROJECT="$1"
	LOCATION="$2"
elif [ $# -eq 1 ]; then
	if [ $1 == "--help" ]; then
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
