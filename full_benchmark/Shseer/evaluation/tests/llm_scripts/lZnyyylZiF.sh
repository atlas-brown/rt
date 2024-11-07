
#!/bin/sh

# Step 1: Read the input CSV file
read -p "Enter the name of the input CSV file: " input_file
if [ ! -f "$input_file" ]; then
  echo "File not found!"
  exit 1
fi

# Step 2: Prompt the user to specify a column to filter by
read -p "Enter the column name to filter by: " column_name

# Step 3: Filter the data based on the specified column
awk -F ',' -v col="$column_name" 'NR==1 { for (i=1; i<=NF; i++) if ($i == col) { col_num=i; break } } NR>1 { if ($col_num == "filter_value") print }' "$input_file" > filtered_data.csv

# Step 4: Output the filtered data to a new file
echo "Filtered data has been saved to filtered_data.csv"
