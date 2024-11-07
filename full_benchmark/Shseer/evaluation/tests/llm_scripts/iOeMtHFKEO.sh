
#!/bin/sh

input_files=("$@")
output_formats=("txt" "html" "docx")  # Example output formats
output_location="/path/to/save/converted/files"

for ((i=0; i<${#input_files[@]}; i++)); do
    input_file="${input_files[$i]}"
    output_format="${output_formats[$i]}"
    output_file="${output_file%.*}.$output_format"
    
    pdftohtml "$input_file" "$output_file"  # Example conversion command

    if [ $? -ne 0 ]; then
        echo "Error converting $input_file to $output_format" >&2
    else
        echo "Converted $input_file to $output_format"
        echo "Converted $input_file to $output_format" >> conversion.log
    fi
done
