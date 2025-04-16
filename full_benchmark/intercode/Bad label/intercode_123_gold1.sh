# Query: search for the word "hello" in all the regular/normal files in the  /workspace folder and display the matched file name

find  /workspace -type f | xargs grep -l "hello"