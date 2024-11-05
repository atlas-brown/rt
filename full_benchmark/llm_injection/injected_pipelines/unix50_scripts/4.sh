# Original: cat $1 | cut -d ' ' -f 1 | sort | uniq -c | sort -r
# Error: The `sort -r -n` command expects numeric input for sorting numerically in reverse order, but the output from `uniq -c` includes both counts and strings (e.g., "5 apple"). This causes a type mismatch because `sort -r -n` cannot correctly interpret the mixed numeric and string data.
cat $1 | cut -d ' ' -f 1 | sort | uniq -c | sort -r -n
