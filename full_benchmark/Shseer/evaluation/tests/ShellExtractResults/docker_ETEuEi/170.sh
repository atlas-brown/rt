#!/bin/bash
cd `dirname $0`

# Run preinstall scripts and install postfix
. ./common-debian-packages/preinstall.sh
apt-get --no-install-recommends -y install postfix sipcalc

# Remove generated certificate and key
rm /etc/ssl/certs/ssl-cert-snakeoil.pem /etc/ssl/private/ssl-cert-snakeoil.key
find /etc/ssl/certs -type l -xtype l -delete

# Run postinstall scripts
. ./common-debian-packages/postinstall.sh
