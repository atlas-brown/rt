# Query: Prints total number of lines of all *.java files in /testbed folder and subfolders.

# @assume "xargs -0 wc -l" --> "(( *[0-9]+ [^\n]+\n)* *[0-9]+ total\n)|( *[0-9]+ [^\n]+\n)"
# @expect "(( *[0-9]+ [^\n]+\n)* *[0-9]+ total\n)|( *[0-9]+ [^\n]+\n)" --> "grep 'total'"
find /testbed -name '*.java' -print0 |xargs -0 wc -l|grep 'total' |awk '{ print $1 }'
