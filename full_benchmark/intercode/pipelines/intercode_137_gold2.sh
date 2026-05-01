# Query: Create a symbolic link in directory "~/newlinks" for each file listed in "/workspace/results.txt"

cat /workspace/results.txt | xargs -I {} ln -s {} ~/newlinks