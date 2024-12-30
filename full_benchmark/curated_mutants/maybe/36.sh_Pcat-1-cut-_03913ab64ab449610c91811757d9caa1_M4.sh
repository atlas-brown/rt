# @assume "cat $1" --> "[0-9]{4}\t[A-Zand\\. ]+\t.+"
cat ${1} | cut -f 2 | cut -d " " -f 1 | sort | sort -nr | uniq -c | head -n 1 | fmt -w1 | sed 1d
