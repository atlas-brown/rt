# Query: Compute the mean average of the word count of *.txt files in the /testbed directory

find /testbed -type f -name "*.txt" -exec wc -w {} + | awk '{total = $1} END {print total/(NR-1)}'