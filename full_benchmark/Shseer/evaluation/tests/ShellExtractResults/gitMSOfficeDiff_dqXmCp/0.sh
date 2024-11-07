#!/bin/bash

echo "Ugh, Excel binaries. Here, compare them yourself."

open -a "Microsoft Excel" "$2"
open -a "Microsoft Excel" "$5" 

# Git will delete $2 on exit (it's a tempfile),
# but $(open) returns immediately without waiting for Excel to finish launching.
# Therefore, stall until we know Excel has the file.
until lsof -a -c "Microsoft Excel" "$2" > /dev/null; do
 	sleep 0.5
done
