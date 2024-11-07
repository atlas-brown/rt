
#!/bin/sh

find /path/to/directory -type f -mtime +30 -exec mv {} /tmp/ \;
