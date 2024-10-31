# Query: Count the *.html files residing in the /testbed directory tree and containing string "foo"

find /testbed -name "*.html" -exec grep -l foo {} + | wc -l