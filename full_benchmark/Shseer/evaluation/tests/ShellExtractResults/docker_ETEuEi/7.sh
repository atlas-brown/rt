#!/bin/bash
export DEBIAN_FRONTEND=noninteractive
echo force-unsafe-io > /etc/dpkg/dpkg.cfg.d/02apt-speedup
apt-get update
apt-get --no-install-recommends -y install php5-fpm php5-mysql php5-imagick php5-mcrypt php5-curl php5-cli php5-memcache php5-intl php5-gd ssmtp

# Cleanup
apt-get clean
rm -f /etc/dpkg/dpkg.cfg.d/02apt-speedup
find /var/lib/apt/lists -mindepth 1 -delete -print
find /tmp /var/tmp -mindepth 2 -delete -print
find /build -delete
