# Query: List all files with their paths that have identical content in /workspace directory

find /workspace -type f | xargs md5sum | sort | uniq -Dw32