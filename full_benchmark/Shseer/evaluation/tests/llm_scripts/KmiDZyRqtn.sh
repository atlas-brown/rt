
#!/bin/sh

# Function to recursively find files based on wildcard matching
find_files() {
  for file in *; do
    if [ -f "$file" ]; then
      echo "$file"
    elif [ -d "$file" ]; then
      cd "$file"
      find_files
      cd ..
    fi
  done
}

# Call the function to start the search
find_files
