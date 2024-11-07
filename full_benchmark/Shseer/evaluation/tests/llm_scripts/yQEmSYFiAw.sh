
#!/bin/sh

# Check if csvkit is installed
if ! command -v csvformat &> /dev/null
then
    echo "csvkit is not installed. Please install csvkit before running this script."
    exit 1
fi

# Check if the input CSV file is provided as an argument
if [ -z "$1" ]
then
    echo "Usage: $0 input.csv output.xlsx"
    exit 1
fi

# Check if the output Excel file is provided as an argument
if [ -z "$2" ]
then
    echo "Usage: $0 input.csv output.xlsx"
    exit 1
fi

# Convert the CSV file to Excel format
csvformat -T -U 0 "$1" > "$2"

echo "CSV file converted to Excel format and saved as $2"
