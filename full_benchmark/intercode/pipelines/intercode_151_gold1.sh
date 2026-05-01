# Query: Uncompress "/workspace/archive.tar.gz" and extract the archive to "/backup"

gzip -dc /workspace/archive.tar.gz | tar -xf - -C /backup