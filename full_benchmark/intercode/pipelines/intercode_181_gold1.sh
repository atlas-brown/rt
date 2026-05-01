# Query: Get the total size of all files in testbed/ and save it to total_size.txt

du -sh testbed/ | awk '{print $1}' > total_size.txt