# Query: Count the number of lines in files under the directory /testbed/dir2.

grep -rl . /testbed/dir2 | xargs wc -l