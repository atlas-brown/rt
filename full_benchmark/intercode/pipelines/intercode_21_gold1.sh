# Query: Count the number of files/directories with '.php' extension under /testbed directory tree and change the permissions to 755

find /testbed -name "*.php" -exec chmod 755 {} \; -exec /bin/echo {} \; | wc -l