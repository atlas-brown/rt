# Query: Convert the first 16 characters in "/testbed/textfile7.txt" to a single hexadecimal value

# @assume "head -n1" --> "[0-9a-f]+( [0-9a-f]{2})+"
# @assume "cut -d' ' -f2-" --> "([0-9a-f]{2} )+"
head /testbed/textfile7.txt -c16 | od -tx1 -w16 | head -n1 | cut -d' ' -f2- | tr -d ' '
