# Query: Copy all files with "FooBar" in the path under the '/testbed' directory to the '/testbed/dir3/subdir1/subsubdir1/tmp' directory.

find /testbed -path '*FooBar*' -print0 | xargs -0 -I{} cp -r {} /testbed/dir3/subdir1/subsubdir1/tmp