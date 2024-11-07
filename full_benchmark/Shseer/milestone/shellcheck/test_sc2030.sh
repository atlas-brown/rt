#!/bin/sh

# A variable was modified in a subshell caused by a pipeline
linecount=0

printf '%s\n' foo bar |
while IFS= read -r line
do
	echo "lines counted $((linecount+=1)) " #Modified here will not be seen
done


echo "total number of lines: $linecount"


