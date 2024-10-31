# Query: Change permissions for all PHP files under the /testbed directory tree to 755 and print the number of files changed

find /testbed -name "*.php" -exec chmod 755 {} \; -exec /bin/echo {} \; | wc -l