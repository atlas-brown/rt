# Query: Convert the first 16 characters in "/testbed/textfile7.txt" to a single hexadecimal value

head /testbed/textfile7.txt -c16 | od -tx1 -w16 | head -n1 | cut -d' ' -f2- | tr -d ' '