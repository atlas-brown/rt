#!/usr/bin/bash

. /lib/svc/share/smf_include.sh
. /lib/sdc/config.sh

load_sdc_sysinfo
load_sdc_config

PATH=/usr/bin:/usr/sbin:${PATH}

tz='Europe/Bucharest'

cat /etc/default/init | grep -v "TZ=" > /etc/default/init.tz
echo "TZ=\"${tz}\"" >> /etc/default/init.tz
mv /etc/default/init.tz /etc/default/init
rm /etc/TIMEZONE
ln -s /etc/default/init /etc/TIMEZONE

exit $SMF_EXIT_OK

