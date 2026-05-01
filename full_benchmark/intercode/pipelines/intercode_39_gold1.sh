# Query: Find .java files in the testbed directory tree that contain 'Hello', and print their names

find /testbed -name "*.java" -exec grep -Hin Hello {} + | cut -d ":" -f 1 | xargs -I{} basename {}