
#!/bin/sh

# Check if the correct number of arguments are provided
if [ "$#" -lt 3 ]; then
  echo "Usage: $0 <input_pdf_file1> <output_format1> <input_pdf_file2> <output_format2> ... <output_directory>"
  exit 1
fi

# Get the output directory
output_dir="${@: -1}"
# Remove the last argument from the list of arguments
set -- "${@:1:$(($#-1))}"

# Loop through the input PDF files and convert them to the desired output format
while [ "$#" -ge 2 ]; do
  input_pdf="$1"
  output_format="$2"
  
  # Check if the input PDF file exists
  if [ ! -f "$input_pdf" ]; then
    echo "Error: Input PDF file '$input_pdf' does not exist"
    shift 2
    continue
  fi
  
  # Convert the input PDF file to the desired output format
  output_file="${output_dir}/$(basename "$input_pdf" .pdf).$output_format"
  if ! pdfto$output_format "$input_pdf" "$output_file"; then
    echo "Error: Failed to convert $input_pdf to $output_format"
  else
    echo "Converted $input_pdf to $output_format and saved as $output_file"
  fi
  
  shift 2
done
