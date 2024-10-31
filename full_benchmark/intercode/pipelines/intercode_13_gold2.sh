# Query: Convert the first 16 characters in "/testbed/textfile7.txt" to a single hexadecimal value

head -c 16 /testbed/textfile7.txt | od -An -tx1 | tr -d ' \n'