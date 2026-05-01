# Query: Copies all files under the /testbed folder like "file.txt" with "FooBar" in the path to the root of the current folder, preserving mode, ownership and timestamp attributes.

find /testbed -type f -path '*FooBar*' | xargs -i cp -p "{}" .