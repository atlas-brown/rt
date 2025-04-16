# Query: Count all the lines of all files with names ending with 'php' in current directory and subdirectories recursively
# @output "[0-9]+"
find . -type f -name '*php' | xargs cat | wc -l
