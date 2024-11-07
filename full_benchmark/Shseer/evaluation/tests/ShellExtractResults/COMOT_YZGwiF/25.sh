#!/bin/sh
echo "Removing mela-data-service"
sudo -S service comot-platform stop
sudo -S rm /etc/init.d/comot-platform
sudo -S update-rc.d -f comot-platform

sudo -S service rSYBL-service stop
sudo -S rm /etc/init.d/rSYBL-service
sudo -S update-rc.d -f rSYBL-service remove

sudo -S rm -rf ./GangliaCFG*
sudo -S rm -rf ./jre1.7.0*
sudo -S rm -rf ./*.tar.gz
sudo -S rm -rf ./COMOT*
sudo -S rm -rf ./WorkloadGeneration-1.0
sudo -S rm -rf ./salsa*

sudo -S ifconfig lo:0 down

