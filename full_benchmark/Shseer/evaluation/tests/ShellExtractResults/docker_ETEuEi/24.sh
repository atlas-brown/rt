#!/bin/sh -x

nginx_site=/etc/nginx/sites-enabled/default

if [ -n "${FRONT_CONTROLLER}" ]
then
    sed -i "s#error_page 404 .*;#error_page 404 ${FRONT_CONTROLLER};#" $nginx_site
    sed -i "s#try_files \$uri \$uri/ /index.html /index.php?\$query_string;#try_files \$uri \$uri/ /index.html /${FRONT_CONTROLLER}?;#" /etc/nginx/sites-enabled/default
fi

# Check to see if a link is defined for "php"
if [ -n "$PHP_NAME" ]
then
    if [ -z "$APP_PORT" ]
    then
        APP_PORT=9000
    fi

    FPM_PORT=`eval echo \\\$PHP_PORT_${APP_PORT}_TCP_PORT`
    FPM_HOST=`eval echo \\\$PHP_PORT_${APP_PORT}_TCP_ADDR`

    if [ -n "$FPM_PORT" -a -n "$FPM_HOST" ]
    then
        echo "Configuring PHP-FPM at $FPM_HOST:$FPM_PORT"
        sed -i "s#fastcgi_pass unix:/var/run/php5-fpm.sock;#fastcgi_pass $FPM_HOST:$FPM_PORT;#g" $nginx_site
    else
        echo "PHP_NAME defined, but incoomplete configuration" >&2
    fi
elif [ -n "$PHP_SOCKET" ]
then
    echo "Configuring PHP socket: $PHP_SOCKET"
    sed -i "s#fastcgi_pass unix:/var/run/php5-fpm.sock;#fastcgi_pass unix:$PHP_SOCKET;#g" $nginx_site
fi

exec /opt/init-nginx.sh
