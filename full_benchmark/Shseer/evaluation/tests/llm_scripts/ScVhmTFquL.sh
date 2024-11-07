
#!/bin/sh

# Remove all empty directories within the specified directory
find /path/to/directory -type d -empty -exec rmdir {} \;
