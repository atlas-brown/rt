# Query: Count the number of differing lines in "/workspace/dir1/long.txt" and "/workspace/dir1/terminate.txt"

diff /workspace/dir1/long.txt /workspace/dir1/terminate.txt | grep ^[\>\<] | wc -l