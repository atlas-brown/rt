#!/usr/bin/bash

. /lib/svc/share/smf_include.sh
. /lib/sdc/config.sh

load_sdc_sysinfo
load_sdc_config

PATH=/usr/bin:/usr/sbin:${PATH}

## Local variables
cfg='/opt/custom/share'

## Functions
function deploy() {
    folder="${cfg}/${1}"

    if [[ -d "${folder}" ]]; then
        # Copy all files from the root-folder
        [[ -d "${folder}/root" ]] && cp -a "${folder}/root/"* /

        # Run all scripts from the script-folder
        if [[ -d "${folder}/script" ]]; then
            for script in "${folder}/script/"*; do
                [[ -x "${script}" ]] && ./${script}
            done
        fi

        # Deploy cronjobs
        [[ -d "${folder}/crontab" ]] && cat "${folder}/crontab/"* | crontab
    fi
}

deploy "global"

exit $SMF_EXIT_OK

