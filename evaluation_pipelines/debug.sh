#!/bin/bash


# curl -s https://api.github.com/repos/Flutterando/slidy/releases | grep browser_download_url | grep "linux-x64[.]tar[.]gz" | head -n 1 | cut -d "\"" -f 4

# echo "${_record_seg}" | tr "}" "a" | cut -d : -f 2

# cat "${dist_dir}"/*.js | grep -q -e "from 'env'" -e "aaa"

# printf "%s" "${3}" | cut -d . -f "2-"

# @assume "cat $1" --> ".* .*"
# @assume "cut -f 2" --> "[0-9]+"
# @assert "head -n 1" --> ".* .* .*"
# @expect "[0-9]+" --> "sort -n"
cat $1 | cut -f 2 | sort -n | uniq -c | sort -nr | head -n 1 | tr -s ' ' '\n' | tail -n 1

# @assume "cat $1" --> ".* .*"
# @assume "cut -f 2" --> "[0-9]+"
# @assert "head -n 1" --> ".* .*"
# @expect "[0-9]+" --> "sort -n"
cat $1 | cut -f 2 | sort -n | uniq -c | sort -nr | head -n 1 | tr -s ' ' '\n' | tail -n 1

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