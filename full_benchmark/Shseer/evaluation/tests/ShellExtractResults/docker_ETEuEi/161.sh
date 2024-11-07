#!/bin/bash

entropy_avail=`cat /proc/sys/kernel/random/entropy_avail`
if [ $entropy_avail -lt 256 ]
then
    echo "Warning: Low amount of entropy available: $entropy_avail"

fi

validates=1
if [ -z "$KEYS_FILE" ]
then
    echo 'Error: $KEYS_FILE (authorized_keys file) undefined'
    validates=0
fi

if [ -z "$KEY_FILE" ]
then
    echo 'Error: $KEY_FILE (private key file) undefined'
fi

if [ $validates -eq 0 ]
then
    exit 255
fi

if [ ! -f "$KEY_FILE" ]
then
    ikeygen_opts=()
    keygen_opts+=(-q)
    keygen_opts+=(-f "$KEY_FILE")

    if [ -n "$PASSPHRASE" ]
    then
        keygen_opts+=(-N "$PASSPHRASE")
    else
        PASSPHRASE=''
        keygen_opts+=(-N '')
    fi

    if [ -n "$KEY_TYPE" ]
    then
	keygen_opts+=(-t "$KEY_TYPE")
    fi

    if [ -n "$KEY_BITS" ]
    then
        keygen_opts+=(-b "$BITS")
    fi

    if [ -n "$KEY_COMMENT" ]
    then
        keygen_opts+=(-C $KEY_COMMENT)
    fi

    if [ -n "$KEYGEN_OPTS" ]
    then
        keygen_opts="$keygen_opts $KEYGEN_OPTS"
    fi

    ssh-keygen "${keygen_opts[@]}"
    echo Generated Key: `ssh-keygen -l -f $KEY_FILE`

    if [ -n "$KEY_USER" ]
    then
	    chown $KEY_USER $KEY_FILE $KEY_FILE.pub
    fi

    if [ -n "$KEY_GROUP" ]
    then
	    chown $KEY_GROUP $KEY_FILE $KEY_FILE.pub
    fi
fi

echo $KEY_OPTIONS `ssh-keygen -y -f $KEY_FILE` $KEY_COMMENT >> $KEYS_FILE
