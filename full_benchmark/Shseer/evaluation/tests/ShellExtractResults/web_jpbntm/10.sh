#!/bin/bash

# Git repository source for customized configuration files
#CONFIG_SOURCE="$(dirname $0)/../system-configs/"
# Target of configuration file updates
#CONFIG_DESTINATION='$HOME'
# Relative path to the configuration files in both SOURCE and DEST folders
#CONFIG_DIR='.config/chromium'

# Kill any existing browser processes
#$(dirname $0)/stop-signs
#sleep 2

# Remove and restore chromium configuration if it has been customized
#rm -rf "$CONFIG_DESTINATION/$CONFIG_DIR"
#if [ -e "$CONFIG_SOURCE/$CONFIG_DIR" ]
#then
#	cp -r "$CONFIG_SOURCE/$CONFIG_DIR" "$CONFIG_DESTINATION/$CONFIG_DIR"
#fi

# Start the signs again
#$(dirname $0)/start-signs
/usr/bin/sudo /usr/sbin/service slides restart &

