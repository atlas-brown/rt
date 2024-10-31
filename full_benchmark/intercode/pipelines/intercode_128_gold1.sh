# Query: Display a long listing of the oldest file under '/workspace' directory tree

find /workspace -type f -printf '%T+ %p\n' | sort | head -n 1 | awk '{print $2}' | xargs ls -l