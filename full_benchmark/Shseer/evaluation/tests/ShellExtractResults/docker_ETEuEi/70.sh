#!/bin/sh
echo "daemon off;" >> /etc/nginx/nginx.conf

# Configure nginx to start as a service
cp -a /build/nginx/init.sh /opt/init-nginx.sh
chmod +x /opt/init-nginx.sh
