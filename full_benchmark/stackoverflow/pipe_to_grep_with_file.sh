#!/bin/bash
# https://stackoverflow.com/questions/50319833/shell-script-to-find-files-with-word1-without-word2

# ---
# tags:   buggy, trivial
# intent: find all files that contain a "word1" but not "word2"
# bug:    input is piped to a grep which is not expecting input from stdin 
# ---

echo -e "File name:"
read file
list=$(find "." -type f -name "$file")
co=$(cat $list | wc -l)
if [ $co -eq 0 ]; then
    echo "File not found"
else
    echo "File(s) List"
    echo "$list"

    # stream enable
    result=$(grep -v "word2" $list | grep -rHn "word1" $list)
    if [ $? -ne 0 ]; then
        echo "Word not found"
    else
        echo "File Line Word"
        echo "$result"
    fi
fi
