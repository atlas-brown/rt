#!/bin/bash

if [[ ! -e "$1" ]]
then
	echo "'$1' not found"
	exit 1
fi

BIN=obj/test
OUTPUT=output.txt

SIMPLE='bst map unordered_map'
HASHED='hashedtree hashedtree-earlyrotate'
FOREST='forest-hashed'

HASH='fnv murmur'
BITS='3 4 6 8 10 12 14 16 18'

rm -f $OUTPUT

for tree in $SIMPLE
do
	$BIN -f "$1" --sim-steps 1000000 --sim-insert-prob 50 -t $tree | tee -a $OUTPUT
done

for tree in $HASHED
do
	for hash in $HASH
	do
		$BIN -f "$1" --sim-steps 1000000 --sim-insert-prob 50 -t $tree --hash $hash | tee -a $OUTPUT
	done
done

for tree in $FOREST
do
	for hash in $HASH
	do
		for bits in $BITS
		do
			$BIN -f "$1" --sim-steps 1000000 --sim-insert-prob 50 -t $tree --hash $hash --bits $bits | tee -a $OUTPUT
		done
	done
done
