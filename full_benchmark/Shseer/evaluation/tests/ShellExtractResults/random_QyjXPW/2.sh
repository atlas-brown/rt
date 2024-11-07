#!/bin/bash

if [[ ! -e "$1" ]]
then
	echo "'$1' not found"
	exit 1
fi

BIN=obj/test
OUTPUT=output-trie.txt

HASH='fnv murmur'
PATTERNS='a b c d e f g h i'
tree=trie

rm -f $OUTPUT

for hash in $HASH
do
	for pattern in $PATTERNS
	do
		$BIN -f "$1" --sim-steps 1000000 --sim-insert-prob 50 -t $tree --hash $hash --pattern $pattern | tee -a $OUTPUT
	done
done
