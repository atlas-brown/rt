# Query: Recursively search for "foo" in the '/system' folder and write the output to the console followed by the number of matched lines

grep -r "foo" /system | awk '{print} END {print NR}'