# Query: Count the number of differing lines in "/workspace/dir1/terminate.txt" and "/workspace/dir1/long.txt" with 0 lines of unified context

diff -U 0 /workspace/dir1/terminate.txt /workspace/dir1/long.txt | grep -v ^@ | wc -l