# Query: Recursively prints all folders in the '/system' folder that contain files like "*.out".

find /system -type f -name "*.out" -printf '%h\n' | sort -u