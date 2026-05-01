# Query: Count the number of unique 3 to 6 character file extensions are in the /workspace directory tree

find /workspace -type f -name '*.*' | sed -n 's/.*\.//p' | awk '{print tolower($0)}' | grep -E '^[a-z]{3,6}$' | sort -u | wc -l