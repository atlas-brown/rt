# Query: Search for the file old2.txt in the /workspace folder and list its permissions and creation time.

find /workspace -name old2.txt | xargs ls -tl