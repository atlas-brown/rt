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
##########################################################################################
#
# About This Script
#
# Name
#	setSearchDomainsForAllNetworkServices.bash
#
# Usage
#	sudo setSearchDomainsForAllNetworkServices.bash
#
# DESCRIPTION
#	Finds all configured network services and sets the designated search domains for each.
#	
#
##########################################################################################
#
# History
#
#	- Created by Miles Leacy on 2016 03 02
#
##########################################################################################
#
# Header ends
#
##########################################################################################
#
# Declare Variables
#
##########################################################################################

# $searchDomains is meant to contain a space-separated list of the computers' intended 
# search domains. For example:
# "subdomain1.domain.ext subdomain2.domain.ext subdomain3.domain.ext domain.ext"

# HARDCODED VALUES ARE SET HERE
$searchDomains=""

# CHECK TO SEE IF A VALUE WAS PASSED IN PARAMETER 4 AND, IF SO, ASSIGN TO "searchDomains"
if [ "$4" != "" ] && [ "$searchDomains" == "" ]
then
    $searchDomains=$4
fi

##########################################################################################
#
# Script begins
#
##########################################################################################

# Save IFS
OLDIFS=$IFS

# Set IFS to newline
IFS=$'\n'

# Loop through configured network services, setting search domains for each
for x in `networksetup -listallnetworkservices | sed 's/*//g' | sed '1d'`
     do
          networksetup -setsearchdomains "$x" $searchDomains
     done

#return IFS to normal
IFS=$OLDIFS

exit 0
