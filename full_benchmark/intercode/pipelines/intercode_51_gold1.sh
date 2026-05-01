# Query: Recursively prints all folders in the '/system' folder that contain files like "*.out".

find /system -type f -name "*.out" -print0 | xargs -0 -n1 dirname | sort -u