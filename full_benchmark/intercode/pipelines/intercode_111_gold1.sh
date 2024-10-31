# Query: print the last word in /workspace/dir1/long.txt

tac /workspace/dir1/long.txt | awk 'NF{print $NF; exit}'