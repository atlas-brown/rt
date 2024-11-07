#!/bin/sh -x

# Use the TZ environment variable, otherwise use UTC
NGINX_DOCROOT=""
if [ -n "${DOCROOT}" ]
then
    APP_ROOT="$DOCROOT"
fi

if [ -z "$APP_ROOT"]
then
    APP_ROOT="/usr/share/nginx/html"
fi

# Update the document root configuration, create the document root if needed
sed -i "s#root .*;#root $APP_ROOT;#" /etc/nginx/sites-enabled/default
mkdir -p $APP_ROOT

. ./common-debian-app/uid-gid-config.sh

# Update the gid of the www-group, if specified
if [ -n "$APP_GID" ]
then
    sed -i "s#^www-data:x:.*:#www-data:x:$APP_GID:#" /etc/group
fi

# Change the uid of the www-data user, if specified
if [ -n "$APP_UID" ]
then
    if [ -z "$APP_GID" ]
    then
        APP_GID=`getent group www-data`
    fi

    echo "Updating www-data ids to ($APP_UID:$APP_GID)"

    sed -i "s#^www-data:x:.*:.*:#www-data:x:$APP_UID:$APP_GID:#" /etc/passwd
    chown www-data /var/log/nginx
fi

exec nginx
