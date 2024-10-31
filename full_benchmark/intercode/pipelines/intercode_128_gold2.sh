# Query: Display a long listing of the oldest file under '/workspace' directory tree

find /workspace -type f -exec stat --format '%Y %n' {} \; | sort -n | head -n 1 | cut -d' ' -f2- | xargs ls -l