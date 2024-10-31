# Query: Copy all files and folders below the /testbed directory whose names contain "FooBar" to directory '/testbed/dir3/subdir1/subsubdir1/tmp'

find /testbed -name '*FooBar*' -print0 | xargs -0 -I{} cp -R {} /testbed/dir3/subdir1/subsubdir1/tmp