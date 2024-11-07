#!/bin/sh

# Listen on all interfaces
sed -i "s#^bind-address\s*=\s*.*#bind-address = 0.0.0.0#" /etc/mysql/my.cnf

# Log to stdout (remove logfile entry)
sed -i 's#^log_error = /var/log/mysql/error.log#console#' /etc/mysql/my.cnf

# key_buffer_size is deprecated
sed -i 's#key_buffer_size =#key_buffer =#g' /etc/mysql/my.cnf

# Configure mysql to start as a service
cd `dirname $0`
cp -a service.sh /opt/init-mysql.sh
chmod +x /opt/init-mysql.sh

cat /dev/null > /var/log/mysql/error.log
