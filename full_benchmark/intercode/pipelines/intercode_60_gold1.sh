# Query: Remove "\r" at the end of each line in "system/folder3/temp/temp1/text1.txt" and display the result as printable characters or backslash escapes

cat /system/folder3/temp/temp1/text1.txt | sed 's/\r$//' | od -c