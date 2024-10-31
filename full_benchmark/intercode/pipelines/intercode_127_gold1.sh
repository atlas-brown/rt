# Query: Create a copy of the /workspace directory structure in the /usr directory,

find /workspace -type d -print|sed 's@^@/usr/@'|xargs mkdir -p