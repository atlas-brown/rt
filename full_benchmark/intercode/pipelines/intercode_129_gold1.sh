# Query: Find the largest 2 directories under /workspace directory

# @assume "xargs -0 du" --> "([0-9]+[ \t]+[^\n]+\n)+"
# @assume "tail -2" --> "([0-9]+[ \t]+[^\n]+\n){1,2}"
# @expect "([0-9]+[ \t]+[^\n]+\n){1,2}" --> "cut -f2"
# @assume "xargs -I{} du -sh {}" --> "([0-9][^ \t\n]*[ \t]+[^\n]+\n)+"
find /workspace -type d -print0 | xargs -0 du | sort -n | tail -2 | cut -f2 | xargs -I{} du -sh {}
