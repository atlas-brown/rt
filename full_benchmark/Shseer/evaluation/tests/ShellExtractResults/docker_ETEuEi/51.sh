#!/bin/sh
# Set up apt for unattended installation
export DEBIAN_FRONTEND=noninteractive
echo force-unsafe-io > /etc/dpkg/dpkg.cfg.d/02apt-speedup

# Install the repository and the packages
command -v apt-add-repository

if [ $? -eq 0 ]
then
	apt-add-repository ppa:formorer/icinga
else
	echo "deb http://ppa.launchpad.net/formorer/icinga/ubuntu trusty main" > /etc/apt/sources.list.d/formorer-icinga-trusty.list
	apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 36862847
fi
apt-get update
apt-get -y install icinga2 ssmtp bsd-mailx

# Clean up
apt-get clean
rm -f /etc/dpkg/dpkg.cfg.d/02apt-speedup
find /tmp /var/tmp -mindepth 2 -delete
