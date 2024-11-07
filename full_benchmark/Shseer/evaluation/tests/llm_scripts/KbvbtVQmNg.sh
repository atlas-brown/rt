
#!/bin/bash

# Set the directory where the CSV files are located
csv_dir="/path/to/csv/files"

# Loop through each CSV file in the directory
for csv_file in $csv_dir/*.csv; do
    # Get the base name of the CSV file
    base_name=$(basename "$csv_file" .csv)
    
    # Convert the CSV file to Excel with specified sheet name and formatting options
    csv2xlsx --sheet-name "$base_name" --formatting-options "option1" "$csv_file" "${base_name}.xlsx"
done
