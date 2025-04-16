# Query: Counts total lines in PHP and JS files in /testbed.

find /testbed -name '*.js' -or -name '*.php' | xargs wc -l | grep 'total'  | awk '{print $1}'