# Query: Print numbers 1 through 10 separated by ":"

yes | head -n10 | grep -n . | cut -d: -f1 | paste -sd: