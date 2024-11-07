#!/bin/sh
# Setup PHP
sed -i -e "s/;daemonize\s*=\s*yes/daemonize = no/g" /etc/php5/fpm/php-fpm.conf
sed -i "s/;cgi.fix_pathinfo=1/cgi.fix_pathinfo=0/" /etc/php5/fpm/php.ini

# Configure PHP (timezone) on startup
cp -a /build/php-fpm/init.sh /etc/my_init.d/00_configure_php.sh
chmod +x /etc/my_init.d/00_configure_php.sh

# Configure PHP-FPM to start as a service
mkdir /etc/service/php-fpm
cp -a /build/php-fpm/runit.sh /etc/service/php-fpm/run
chmod +x /etc/service/php-fpm/run
php5enmod mcrypt

# Ensure the mode is correct on the unix socket
sed -i 's#;listen.mode = 0660#listen.mode = 0666#g' /etc/php5/fpm/pool.d/www.conf

# Disable xdebug by default
php5dismod xdebug
