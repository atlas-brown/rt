# Query: Unpack all *.gz archives in the /workspace directory tree

find /workspace -name '*.gz' -print0 | xargs -0 gunzip