#!/bin/sh
mkdir -p "outputs"
for file in tests/*.json; do
	[ -e "$file" ] || continue
	basename="${file##*/}"
	output_file="outputs/$basename"

	bin/json_merger "$file" --javascript --pretty > "$output_file"

	if diff -q "expected_outputs/$basename" "$output_file"; then
		printf ".fromFile: %s passed test\n" "$file"
	else
		exit 1
	fi

	node -e 'var fs = require("fs");
		var path = require("path");
		var json_merger = require("./json_merger.js");
		var json = json_merger.parseFile(process.argv[1], {
			javascript: true
		});
		var output = json_merger.fromObject(json, {
			javascript: true,
			scope: path.dirname(process.argv[1])
		});
		console.log(json_merger.stringify(output, {
			asText: "pretty",
			javascript: true
		}));
		' "$file" > "$output_file"

	if diff -q "expected_outputs/$basename" "$output_file"; then
		printf ".fromObject: %s passed test\n" "$file"
	else
		exit 1
	fi
done
