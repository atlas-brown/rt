# Query: Print all unique file paths under "testbed/dir1" compared to "testbed/dir2"

comm -23 <(find testbed/dir1 -type f | sed 's|testbed/dir1/||' | sort) <(find testbed/dir2 -type f | sed 's|testbed/dir2/||' | sort) | sed 's|^|testbed/dir1/|'