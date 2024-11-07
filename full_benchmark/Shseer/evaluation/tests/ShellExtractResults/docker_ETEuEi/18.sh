#!/bin/sh

# Use the TZ environment variable, otherwise use UTC
PHP_TIMEZONE="UTC"
if [ -n "${TZ}" ]
then
    PHP_TIMEZONE="$TZ"
fi

find /etc/php5 -name php.ini -print0 | xargs -0 sed -i "s#;date.timezone =.*#date.timezone = $PHP_TIMEZONE#"

if [ ! -z "$DEBUG" ]
then
	php5enmod xdebug
	sed -i 's#^display_errors = Off#display_errors = On#' /etc/php5/fpm/php.ini
fi

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

# Grep for variables that look like docker set them (_PORT_)
for file in /etc/container_environment/*
do
    var=$(basename $file)
    val=$(cat $file)
    echo $var $val
    set_phpfpm_env_var $var $val
done
