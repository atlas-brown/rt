# Query: Change permissions for all PHP files under the /testbed directory tree to 755 and print the number of files changed

find /testbed -type f -name "*.php" -exec chmod 755 {} \; -print | wc -l