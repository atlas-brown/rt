#!/usr/bin/bash

. /lib/svc/share/smf_include.sh
. /lib/sdc/config.sh

load_sdc_sysinfo
load_sdc_config

rem_drv ugen
add_drv -i '"usb665,5161.2"' -m '* 0666 nut root' ugen
update_drv -a -m '* 0666 nut root' -i '"usb665,5161.2"' ugen

exit $SMF_EXIT_OK

