#!/bin/sh
# Set up apt for unattended installation
# Install the repository and the packages
command -v apt-add-repository

if [ $? -eq 0 ]
then
	apt-add-repository ppa:formorer/icinga
else
	echo "deb http://ppa.launchpad.net/formorer/icinga/ubuntu trusty main" > /etc/apt/sources.list.d/formorer-icinga-trusty.list
	apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 36862847
fi
