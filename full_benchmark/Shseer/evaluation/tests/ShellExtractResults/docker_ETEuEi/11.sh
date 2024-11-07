#!/bin/sh

cd `dirname $0`

# Update the listen address for PHP_FPM
if [ -z "${LISTEN}"]
then
    LISTEN=9000
fi

sed -i "s#^listen = .*#listen = $LISTEN#g" /etc/php5/fpm/pool.d/www.conf

find /etc/php5 -name php.ini -print0 | xargs -0 sed -i "s#;date.timezone =.*#date.timezone = $PHP_TIMEZONE#"

. ./configure-php-ini.sh
. ./configure-fpm-user.sh
. ./configure-fpm-environment.sh

exec php5-fpm -c /etc/php5/fpm
