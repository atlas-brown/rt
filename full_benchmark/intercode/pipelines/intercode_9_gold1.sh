# Query: Compute the mean average of the word count of *.txt files in the /testbed directory

find /testbed -name '*.txt' -print0 | xargs -0 wc -w | awk 'END { print $1/(NR-1) }'