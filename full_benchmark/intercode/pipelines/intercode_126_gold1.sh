# Query: Count the number of unique 3 to 6 character file extensions are in the /workspace directory tree

find /workspace -type f -name '*.*' | awk -F. 'NF>1 {ext=tolower($NF); if (length(ext) >= 3 && length(ext) <= 6) print ext}' | sort | uniq -c | wc -l