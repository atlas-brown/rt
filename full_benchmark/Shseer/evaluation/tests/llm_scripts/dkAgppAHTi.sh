
#!/bin/sh

for config in $1
do
    logrotate $config
done

for dir in $2
do
    tar -czvf $dir/logs.tar.gz $dir/*.log.1
done
