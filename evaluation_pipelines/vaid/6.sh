cat $1 \
	| grep -v '^#' \
	| sed 's/^[^<]*<\([^>]*\)>/\1/' \
	| grep '<.*>' | sed -e 's/[<>]/ /g' \
	| awk '{if ($3 != "") { print $3" "$1 } else {print $2" "$1}}' \
	| sort | uniq