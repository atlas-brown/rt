# Query: Remove everything within parentheses and substitute all non digit characters with a space from "1/2 [3] (27/03/2012 19:32:54) word word word word 4/5" and format the output as a table

# @assume "echo '1/2 [3] (27/03/2012 19:32:54) word word word word 4/5'" --> ".*\\(.*\\).*"
echo '1/2 [3] (27/03/2012 19:32:54) word word word word 4/5' | sed -e 's/(.*)//' -e 's/[^0-9]/ /g' | column -t
