#!/bin/sh
# Add environment variables to the php-fpm configuration
# Based on startup.sh from https://github.com/dubture-dockerfiles/nginx-php

set_phpfpm_env_var() {
    if [ -z "$2" ]
    then
            echo "Environment variable '$1' not set."
            return
    fi

    # Check whether variable already exists
    if grep "^env\[$1\]=" /etc/php5/fpm/pool.d/www.conf
    then
        sed -i "s#^env\[$1\]=.*#env[$1]=\"$2\"#g" /etc/php5/fpm/pool.d/www.conf
    else
        echo "env[$1]=\"$2\"" >> /etc/php5/fpm/pool.d/www.conf
    fi
}

for var in `env | egrep -v -f /opt/php-fpm/setup-env | cut -d= -f1`
do
    val=`eval 'echo "$'"$var"'"'`
    set_phpfpm_env_var $var $val
done
