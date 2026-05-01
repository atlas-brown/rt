# Query: Display the sizes and filepaths of all files/directories in /workspace directory sorted in descending order of size

# @assume "du -ah /workspace" --> "([0-9][^ \t\n]*[ \t]+[^\n]+\n)+"
du -ah /workspace | sort -rh
