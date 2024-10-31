# Query: Recursively finds all files containing text 'Hello' in /testbed and prints folder where they are placed.

grep -rl 'Hello' /testbed | xargs -I {} dirname {} | sort | uniq