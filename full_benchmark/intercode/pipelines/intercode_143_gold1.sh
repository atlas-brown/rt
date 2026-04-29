# Query: Display the sizes and filepaths of all files/directories in /workspace directory sorted in descending order of size

# @assume "du /workspace -a -h" --> "([0-9][^ \t\n]*[ \t]+[^\n]+\n)+"
du /workspace -a -h | sort -hr
