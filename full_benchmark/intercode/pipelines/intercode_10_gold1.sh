# Query: Compute the mean average of the word count of *.txt files smaller than 6 words in the /testbed directory

find /testbed -name '*.txt' -print0 | xargs -0 wc -w | awk '$1 < 6 {v += $1; c++} END {print v/c}'