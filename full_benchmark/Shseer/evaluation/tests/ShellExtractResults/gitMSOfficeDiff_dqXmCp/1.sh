#!/bin/bash

for i in `unzip -Z -1 "$1"`; do
	echo "$i"
	unzip -a -p "$1" '\'"$i" | xmllint --format -
done
