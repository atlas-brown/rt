#!/bin/bash

# Read collected.txt and split by comma into lines
files=$(cat collected/collected.txt | tr "," "\n")

# Create target directories if they don't exist
mkdir -p collected/pre_commit
mkdir -p collected/post_commit

#!/bin/bash

# Read collected.txt and split by comma into lines
tr "," "\n" < collected/collected.txt | while IFS= read -r file; do
    # Trim whitespace from filename
    file=$(echo "$file" | xargs)
    
    # Skip empty lines
    if [ -z "$file" ]; then
        continue
    fi
    
    # Check if file exists in output_new/pre_commit
    if [ -f "output_new/pre_commit/$file" ]; then
        cp "output_new/pre_commit/$file" "collected/pre_commit/$file"
        echo "Copied output_new/pre_commit/$file to collected/pre_commit/"
    fi
    
    # Check if file exists in output_new/post_commit
    if [ -f "output_new/post_commit/$file" ]; then
        cp "output_new/post_commit/$file" "collected/post_commit/$file"
        echo "Copied output_new/post_commit/$file to collected/post_commit/"
    fi
done

echo "File collection complete."