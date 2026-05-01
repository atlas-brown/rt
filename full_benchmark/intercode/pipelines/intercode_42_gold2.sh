# Query: Recursively finds all files containing text 'Hello' in /testbed and prints folder where they are placed.

find /testbed -type f -exec grep -l 'Hello' {} + | xargs -I {} dirname {} | sort | uniq