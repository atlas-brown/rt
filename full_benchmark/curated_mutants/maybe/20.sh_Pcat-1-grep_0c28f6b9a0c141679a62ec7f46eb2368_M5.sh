# @file "$1": "[A-Za-z,\\. ]+ (\([A-Za-z,\\. ]+\) )*|[0-9]+"
# @output "[A-Za-z,\\. ]+"
cat ${1} | cut -d "(" -f 2 | cut -d ")" -f 1 | head -n 1
