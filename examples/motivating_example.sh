find . | # Find files
grep -E 'book[0-9]+\.txt' | # Filter by name
xargs cat | # Concat files
tr -cs A-Za-z '\n' | # Split words
tr '[:lower:]' '[:upper:]' | # Normalize
grep -fw dict.txt | # Filter words
sort | uniq | sort -rn