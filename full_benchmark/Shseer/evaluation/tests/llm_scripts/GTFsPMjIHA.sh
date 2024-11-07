
#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 3 ]; then
  echo "Usage: $0 <xml_file> <data_to_extract> <new_element>"
  exit 1
fi

xml_file=$1
data_to_extract=$2
new_element=$3

# Extract specific data from the XML file
extracted_data=$(grep "<$data_to_extract>" $xml_file | sed -e "s/<$data_to_extract>//" -e "s/<\/$data_to_extract>//")

# Modify the XML file by adding or updating elements
if grep -q "<$data_to_extract>" $xml_file; then
  # Update existing element
  sed -i "s|<$data_to_extract>.*<\/$data_to_extract>|<$data_to_extract>$new_element<\/$data_to_extract>|" $xml_file
else
  # Add new element
  sed -i "/<root>/a $new_element" $xml_file
fi

echo "Data extracted: $extracted_data"
echo "XML file modified with new element: $new_element"
