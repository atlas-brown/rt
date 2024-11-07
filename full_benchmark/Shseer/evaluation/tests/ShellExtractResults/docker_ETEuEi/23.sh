#!/bin/sh
cp -a /build/nginx-php/site-default /etc/nginx/sites-available/default
cp -a /build/nginx-php/init.sh /opt/init-nginx-php.sh
chmod +x /opt/init-nginx-php.sh
