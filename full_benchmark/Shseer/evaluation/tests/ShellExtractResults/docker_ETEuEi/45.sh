#!/bin/sh
# Set up apt for unattended installation
export DEBIAN_FRONTEND=noninteractive
echo force-unsafe-io > /etc/dpkg/dpkg.cfg.d/02apt-speedup

apt-get update
apt-get --no-install-recommends -y install icinga2-ido-mysql

# Clean up
apt-get clean
rm -f /etc/dpkg/dpkg.cfg.d/02apt-speedup
find /var/lib/apt/lists -mindepth 1 -delete -print
find /tmp /var/tmp -mindepth 2 -delete -print
find /build -delete
