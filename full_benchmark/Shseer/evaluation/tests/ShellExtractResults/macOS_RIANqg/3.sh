#!/bin/bash
#
##########################################################################################
#
# Header begins
#
##########################################################################################
#
# Copyright (c) 2016, Miles A. Leacy IV.  All rights reserved.
#
#     This script may be copied, modified, and distributed freely as long as this header
#     remains intact and modifications are publicly shared with the Mac administrators'
#     community at large.
#
#     This script is provided "as is".  The author offers no warranty or guarantee of any
#     kind.
#
#     Use of this script is at your own risk.  The author takes no responsibility for loss
#     of use, loss of data, loss of job, loss of socks, the onset of armageddon, or any
#     other negative effects.
#
#     Test thoroughly in a lab environment before use on production systems.
#     When you think it's ok, test again.  When you're certain it's ok, test twice more.
#
###########################################################################################
#
# About This Script
#
# Name
#	removeSsidFromPreferredList.bash
#
# Usage
#	sudo removeSsidFromPreferredList.bash
#
# DESCRIPTION
#	Removes a given SSID from the preferred wireless networks list.
#	* IF computer is not connected to the SSID AND the SSID is in the preferred
#		networks list, this script removes the SSID from the preferred networks list.
#
# VARIABLES
#	targetNetwork
#		SSID to be removed. May be hardcoded or provided by parameter 4
#
#	wirelessPort
#		device name of wireless network port
#
#	currentNetwork
#		SSID the computer is connected to at runtime
#
#	targetPreferred
#		is targetNetwork in the preferred networks list? 0 = no
#
##########################################################################################
#
# History
#
#	- Created by Miles Leacy on 2016 03 13
#
##########################################################################################
#
# Header ends
#
##########################################################################################

# redirect stderr to stdout
exec 2>&1

##########################################################################################
#
# Declare Variables
#
##########################################################################################

# define the network SSID to be removed
targetNetwork=""

	# CHECK TO SEE IF A VALUE WAS PASSED IN PARAMETER 4 AND, IF SO, ASSIGN TO "targetNetwork"
		if [ "$4" != "" ] && [ "$targetNetwork" == "" ]
			then
				targetNetwork=$4
		fi

# get device name of wireless interface
wirelessPort=$(networksetup -listallhardwareports | awk '/Wi-Fi|AirPort/{getline; print $NF}')

# get current wireless network
currentNetwork=$(networksetup -getairportnetwork "$wirelessPort" | awk '{print $4}')

# is targetNetwork in the preferred network list?
targetPreferred=$(networksetup -listpreferredwirelessnetworks "$wirelessPort" | awk '/'"$targetNetwork"'/{x++;}END{print x}')

##########################################################################################
#
# Script begins
#
##########################################################################################

if [ "$currentNetwork" != "$targetNetwork" ] && [ "$targetPreferred" -ne 0 ]
	then
		networksetup -removepreferredwirelessnetwork $wirelessPort $targetNetwork
fi

exit 0
