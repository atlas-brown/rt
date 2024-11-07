#!/bin/sh
echo " >> Configuring Runit"
mkdir /etc/service/icinga2
cp -av /build/icinga2/runit.sh /etc/service/icinga2/run
chmod +x /etc/service/icinga2/run
