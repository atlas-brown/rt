# Query: Print the number of python files in the testbed directory.

find testbed -type f -name "*.py" | wc -l