
#!/bin/sh

for dir in $(echo $PATH | tr ':' ' '); do
    echo "Directory: $dir"
    echo "Number of executable files: $(find $dir -maxdepth 1 -type f -executable | wc -l)"
done
