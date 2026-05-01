#!/bin/bash
[[ -n "$input_file" ]] || echo "script was not provided with \$input_file"
[[ -n "$statistics_dir" ]] || echo "script was not provided with \$statistics_dir"

# @file "$input_file": ".{88}[0-9]{4}.*"
cat "${input_file}" |
  cut -c 89-92 |
  grep -v 999 |
  sort -rn |
  head -n1 > ${statistics_dir}/max.txt

# @file "$input_file": ".{88}[0-9]{4}.*"
cat "${input_file}" |
  cut -c 89-92 |
  grep -v 999 |
  sort -n |
  head -n1 > ${statistics_dir}/min.txt

# @file "$input_file": ".{88}[0-9]{4}.*"
cat "${input_file}" |
  cut -c 89-92 |
  grep -v 999 |
  awk "{ total += \$1; count++ } END { print total/count }" > ${statistics_dir}/average.txt 
