#!/bin/sh

# Set the timezone using the Use the TZ environment variable, otherwise use UTC
PHP_TIMEZONE="UTC"
if [ -n "${TZ}" ]
then
    PHP_TIMEZONE="$TZ"
fi

find /etc/php5 -name php.ini -print0 | xargs -0 sed -i "s#;date.timezone =.*#date.timezone = $PHP_TIMEZONE#"
