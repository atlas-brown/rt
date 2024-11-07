
#!/bin/sh

echo "Enter the name of the CSV file: "
read filename

if [ -f $filename ]; then
    echo "Enter the name of the column to filter by: "
    read column

    if [ $(head -n 1 $filename | tr ',' '\n' | grep -c -w $column) -eq 1 ]; then
        echo "Enter the value to filter by: "
        read value

        awk -F, -v col="$column" -v val="$value" '$col == val' $filename > filtered_data.csv
    else
        echo "Column does not exist in the CSV file."
    fi
else
    echo "File does not exist."
fi
