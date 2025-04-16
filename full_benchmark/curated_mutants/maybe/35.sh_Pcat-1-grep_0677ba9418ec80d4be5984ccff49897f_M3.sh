# @assume "cat $1" --> "[0-9]{4}\t[A-Za-z \"'-]+\t(Male|Female)\t[A-Za-z ]+\t[A-Za-z ]*\t[0-9]{4}\t[A-Za-z ,().'-]+|[0-9]+"
# @output "[0-9]{4}"
cat ${1} | cut -f 1
