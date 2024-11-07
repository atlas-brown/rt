#!/bin/bash
echo "- Removing dependency_libs fields..."
filename=""
for filename in `find debian/ -name "*.la"`; do
	echo "  - $filename"
	mv "$filename" "$filename.tmp"
	sed "s/^dependency_libs=.*/dependency_libs=''/" < "$filename.tmp" > "$filename"
	chmod --reference="$filename.tmp" "$filename"
	rm "$filename.tmp"
done

