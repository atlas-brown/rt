# Query: Create logs.tar.gz of all older than one day logs of Ubuntu

find /var/log/ -mtime +1 | xargs  tar -czvPf  /testbed/logs.tar.gz