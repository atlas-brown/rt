# Query: Print "True" if the contents of file /testbed/dir3/subdir1/subsubdir1/textfile3.txt is a subset of file /testbed/dir2/subdir1/textfile2.txt, otherwise print "False"

comm -23 <(sort /testbed/dir3/subdir1/subsubdir1/textfile3.txt | uniq) <(sort /testbed/dir2/subdir1/textfile2.txt | uniq) | head -1 | grep -q '.' && echo "False" || echo "True"