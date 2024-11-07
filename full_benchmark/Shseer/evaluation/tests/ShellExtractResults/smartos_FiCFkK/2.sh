#!/usr/bin/bash
# Author: hugo@freenode

#save_us=( /etc/passwd /etc/shadow /etc/group /etc/ouser_attr /etc/user_attr /etc/security/policy.conf /etc/security/auth_attr /etc/security/exec_attr /etc/security/prof_attr /etc/motd )
save_us=( /etc/passwd /etc/group /etc/motd )

ukeystor="/opt/custom/share/global/system"

# this script needs rsync
if [ ! -f /usr/bin/rsync ]; then
    echo please install rsync
    exit 1
fi

case "$1" in
    'start')
    if [[ -n $(/bin/bootparams | grep '^smartos=true') ]]; then
        for file in ${save_us[*]}
        do
            ukf=${ukeystor}${file}

            if [[ -z $(/usr/sbin/mount -p | grep $file) ]]; then
                if [[ $ukf -ot $file ]]; then
                    rsync -Rrtpogu $file $ukeystor
                    echo "sys->stor: $file"
                else
                    rsync -rtpog $ukf $file
                    echo "stor->sys: $file"
                fi

            touch $file $ukf
            mount -F lofs $ukf $file
            fi
       done
    fi
    ;;
    'stop')
        for file in ${save_us[*]}
        do
            if [[ -n $(/usr/sbin/mount -p | grep $file) ]]; then
                umount $file && touch $file
            fi
        done
    ;;
esac
