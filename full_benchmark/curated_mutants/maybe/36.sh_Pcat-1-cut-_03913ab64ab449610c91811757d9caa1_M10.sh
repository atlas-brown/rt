# @assume "cat $1" --> "[0-9]{4}\t[A-Zand\\. ]+\t.+"
# @expect "[A-Z]+" --> "sort"
cat ${1} | cut -f 2 | sort | uniq -c | sort -nr | head -n 1 | fmt -w1 | sed 1d
