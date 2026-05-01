# Query: Display the five biggest file sizes only in the /testbed directory

ls -lS /testbed | grep '^-' | head -n 5