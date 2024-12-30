# @assume "cat $1" --> "[0-9]{4}\t[A-Za-z \"'-]+\t(Male|Female)\t[A-Za-z ]+\t[A-Za-z ]*\t[0-9]{4}\t[A-Za-z ,().'-]+"
# @expect ".*Bell.*" --> "cut -f 2"
cat ${1} | sed 1d | cut -f 2
