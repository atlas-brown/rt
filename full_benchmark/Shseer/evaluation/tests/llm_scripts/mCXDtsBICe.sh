
#!/bin/sh

input_file=$1
split_pattern=$2
output_naming=$3

if grep -q $split_pattern $input_file; then
    csplit $input_file $split_pattern -n 1 -f $output_naming
else
    echo "Pattern not found in input file"
fi
