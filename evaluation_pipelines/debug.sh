#!/bin/bash

# cat a.txt | xargs echo

cat ${IN}/${input} | tr "[a-z]" "[A-Z]" | tr -sc "BCDFGHJKLMNPQRSTVWXYZ" "[\\012*]" | sort | uniq -c >${OUT}/${input}.out

cat a.txt | sort | uniq -c | sort

# ls | xargs cat

# cat a.txt | grep "a" | grep "a"

# cat a.txt | grep "a" | grep -v "a"

# cat a.txt | grep -v "a" | grep -v "ab"

${LDCONFIG} -p | grep libstdc++.so.6 | grep 64

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu   $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list >/dev/null

# grep 'git' go.mod | grep '\.com' | grep -v indirect | grep -v replace | cut -f 2 | cut -d ' ' -f 1 | while read line; do
#   go get -u "$line"
#   make vendor
#   git add .
#   git commit -m "update $line"
# done

# sed --version 2>/dev/null | grep -q GNU

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