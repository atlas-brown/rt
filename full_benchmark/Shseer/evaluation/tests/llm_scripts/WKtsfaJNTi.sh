
#!/bin/sh

# Check if the required command line arguments are provided
if [ $# -ne 3 ]; then
  echo "Usage: $0 <input_pdf_file> <output_format> <output_location>"
  exit 1
fi

input_pdf="$1"
output_format="$2"
output_location="$3"

# Convert the PDF to the desired format and save it to the specified location
pdftoppm -format "$output_format" "$input_pdf" "$output_location"
