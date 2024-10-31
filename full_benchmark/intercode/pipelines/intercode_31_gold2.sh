# Query: Counts total lines in PHP and JS files in /testbed.

find /testbed -type f \( -name '*.php' -o -name '*.js' \) -exec wc -l {} + | awk '{s=$1} END {print s}'