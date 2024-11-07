#!/bin/sh

# Use the TZ environment variable, otherwise use UTC
NGINX_DOCROOT="/var/www"
if [ -n "${DOCROOT}" ]
then
    NGINX_DOCROOT="$DOCROOT"
fi

sed -i "s#root .*;#root $NGINX_DOCROOT;#" /etc/nginx/sites-enabled/default
mkdir -p $NGINX_DOCROOT

if [ -n "${FRONT_CONTROLLER}" ]
then
    sed -i "s#error_page 404 .*;#error_page 404 ${FRONT_CONTROLLER};#" /etc/nginx/sites-enabled/default
    sed -i "s#try_files \$uri \$uri/ /index.html /index.php?\$query_string;#try_files \$uri \$uri/ /index.html /${FRONT_CONTROLLER}?;#" /etc/nginx/sites-enabled/default
fi

if [ $SYNC_UID -eq 1 ]
then
    uid=`stat -c '%u' $DOCROOT`
    gid=`stat -c '%g' $DOCROOT`
    
    echo "Updating www-data ids to ($uid:$gid)"

    if [ ! $uid -eq 0 ]
    then
        sed -i "s#^www-data:x:.*:.*:#www-data:x:$uid:$gid:#" /etc/passwd
    fi

    if [ ! $gid -eq 0 ]
    then
        sed -i "s#^www-data:x:.*:#www-data:x:$gid:#" /etc/group
    fi

    chown www-data /var/log/nginx
fi
