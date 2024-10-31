# Query: Count all the lines of all files with names ending with 'php' in current directory and subdirectories recursively

find . -type f -name '*.php' -exec wc -l {} + | awk '{s=$1} END {print s}'