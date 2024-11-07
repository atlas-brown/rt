
#!/bin/bash

# Check if the correct number of arguments are provided
if [ "$#" -ne 2 ]; then
  echo "Usage: $0 <xml_file> <xpath_query>"
  exit 1
fi

xml_file=$1
xpath_query=$2

# Use xmlstarlet to extract specific data from the XML file
xmlstarlet sel -t -v "$xpath_query" "$xml_file"
