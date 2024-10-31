# Query: Search for the file old2.txt in the /workspace folder and list its permissions and creation time.

find /workspace -name old2.txt -print0 | xargs -0 ls -tl