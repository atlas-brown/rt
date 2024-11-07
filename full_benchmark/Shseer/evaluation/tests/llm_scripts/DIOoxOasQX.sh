
#!/bin/sh

# Use find command to locate all .swp files in the system and exclude directories with improper permissions
find / -type f -name "*.swp" ! -perm /u=rwx,g=rwx,o=rwx -delete
