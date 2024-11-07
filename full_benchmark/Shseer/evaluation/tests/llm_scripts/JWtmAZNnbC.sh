
#!/bin/bash

# Remove empty directories
find /path/to/directory -type d -empty -delete

# Archive and compress old files
find /path/to/directory -type f -mtime +30 -exec tar -czf {}.tar.gz {} \;

# Move specific file types to designated directories
find /path/to/directory -type f -name "*.txt" -exec mv {} /path/to/text_files_directory \;
find /path/to/directory -type f -name "*.jpg" -exec mv {} /path/to/image_files_directory \;

# Log all actions taken
echo "Empty directories removed: $(date)" >> /path/to/log_file
echo "Old files archived and compressed: $(date)" >> /path/to/log_file
echo "Text files moved to designated directory: $(date)" >> /path/to/log_file
echo "Image files moved to designated directory: $(date)" >> /path/to/log_file
