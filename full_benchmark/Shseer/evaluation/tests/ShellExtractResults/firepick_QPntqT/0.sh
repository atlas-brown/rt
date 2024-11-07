#!/bin/bash

if [ $EUID != 0 ]; then
		sudo "$0" "$@"
		exit $?
fi

apt-get install \
		python-dev \
		python-setuptools \
		python-pip \
		rpi.gpio

pip install rpi.gpio

mkdir -v /opt/firepick-delta-console
cp -v ./Adafruit_CharLCD.py /opt/firepick-delta-console/
cp -v ./LCD_SystemInfo.py /opt/firepick-delta-console/
cp -v ./lcd /etc/init.d/
chmod -v +x /opt/firepick-delta-console/Adafruit_CharLCD.py
chmod -v +x /opt/firepick-delta-console/LCD_SystemInfo.py
chmod -v +x /etc/init.d/lcd
update-rc.d lcd defaults
