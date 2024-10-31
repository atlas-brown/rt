# Query: Search for 'hello' case insensitively in all files under /workspace directory tree and show the matched lines with their filenames

find /workspace -type f -print0  | xargs -0 grep -iH "hello"