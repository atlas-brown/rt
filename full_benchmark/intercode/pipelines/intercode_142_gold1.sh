# Query: Display the last slash-separated part of each filename path in /workspace/dir1/file.txt

rev /workspace/dir1/file.txt | cut -d/ -f1 | rev