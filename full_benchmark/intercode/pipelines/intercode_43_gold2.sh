# Query: Prints total number of lines of all *.java files in /testbed folder and subfolders.

find /testbed -name "*.java" -exec wc -l {} + | awk '{s=$1} END {print s}'