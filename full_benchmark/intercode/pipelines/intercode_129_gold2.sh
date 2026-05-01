# Query: Find the largest 2 directories under /workspace directory

# @assume "xargs -0 du" --> "([0-9]+[ \t]+[^\n]+\n)+"
find /workspace -type d -print0 | xargs -0 du | sort -n | tail -2
