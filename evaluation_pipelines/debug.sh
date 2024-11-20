#!/bin/bash

# Pipeline in assignment - counts number of text files in current directory
# and stores result in a variable
file_count=$(find . -type f -name "*.txt" | wc -l)

# Function that uses a pipeline to search for a pattern in files
# and format the output
search_files() {
    local pattern="$1"
    local directory="${2:-.}"  # Default to current directory if not specified
    
    find "$directory" -type f -name "*.txt" |
        while read -r file; do
            grep -l "$pattern" "$file" |
                xargs -I {} basename {} |
                    sed 's/\.txt$//'
        done | sort
}

# Print the count of text files
echo "Number of text files found: $file_count"

# Example usage of the function
echo -e "\nFiles containing 'example' (without .txt extension):"
search_files "example"

# Example with different pattern and directory
echo -e "\nFiles containing 'test' in /tmp (without .txt extension):"
search_files "test" "/tmp"