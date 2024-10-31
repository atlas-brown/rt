# Query: Find all files modified in the last 2 hours and compress them into a tarball named archive.tar.gz in the directory /testbed

find /testbed -type f -mmin -120 -print0 | xargs -0 tar -czf /testbed/archive.tar.gz