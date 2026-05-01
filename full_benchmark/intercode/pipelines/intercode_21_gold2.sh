# Query: Count the number of files/directories with '.php' extension under /testbed directory tree and change the permissions to 755

find /testbed -type f -name '*.php' -exec chmod 755 {} \; -print | wc -l