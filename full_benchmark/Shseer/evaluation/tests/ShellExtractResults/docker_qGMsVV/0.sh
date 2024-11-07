#!/bin/bash

WEECHAT_UID=1000
WEECHAT_GID=1000

WEECHAT_USER=weechat
WEECHAT_HOME=/weechat

if [[ -z $IRC_SERVER ]]; then
    IRC_SERVER=localhost
fi

if [[ -z $USER ]]; then
    echo "No \$USER env set, defaulting to USER=$WEECHAT_USER"
else
    echo "Using USER $USER."
    WEECHAT_USER=$USER
fi

if [[ ! -e $WEECHAT_HOME ]]; then
    echo "No $WEECHAT_HOME bind mount detected, creating throwaway directory."
    mkdir $WEECHAT_HOME
else
    echo "Bind mount $WEECHAT_HOME found."
    WEECHAT_UID=$(ls -nd $WEECHAT_HOME | awk '{ print $3 }')
    WEECHAT_GID=$(ls -nd $WEECHAT_HOME | awk '{ print $4 }')
fi

echo "Setting up user ($WEECHAT_USER) to run weechat."
addgroup --gid $WEECHAT_GID $WEECHAT_USER &> /dev/null
adduser --uid $WEECHAT_UID --gid $WEECHAT_GID $WEECHAT_USER --home $WEECHAT_HOME --no-create-home --disabled-password --gecos '' &> /dev/null

if [[ $IRC_SERVER == "localhost" ]]; then
    mkdir -p $WEECHAT_HOME/bitlbee
    chmod 700 $WEECHAT_HOME/bitlbee
    chown -R ${WEECHAT_USER}.${WEECHAT_USER} $WEECHAT_HOME/bitlbee
fi

chown ${WEECHAT_USER}.${WEECHAT_USER} $WEECHAT_HOME

if [[ $IRC_SERVER == "localhost" ]]; then
    echo "Starting bitblee."
    su - $WEECHAT_USER -c "/usr/sbin/bitlbee"

    echo "Waiting for bitblee to start."
    sleep 2
fi

echo "Running weechat."
export TERM=xterm-256color

if [[ -z $NO_AUTO_CONNECT ]]; then
    SERVER_ARG="irc://$IRC_SERVER/"
else
    SERVER_ARG=""
fi

su - $WEECHAT_USER -c "LC_ALL=en_US.utf8 weechat $SERVER_ARG"

if [[ $IRC_SERVER == "localhost" ]]; then
    echo "Killing bitblee."
    pkill bitlbee

    echo "Waiting for bitblee to end."
    sleep 2
fi
