# Query: Move files in /workspace accessed less than one day ago to directory /.

find /workspace -type f -atime -1 -print0 | xargs -0 -I {} mv {} /