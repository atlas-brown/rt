#!/usr/bin/env bash

################################################################################
# Commit message: Only get the first gateway for chronometer  Signed-off-by: Mark Drobnak <mark.drobnak@gmail.com>
# Commit URL: https://github.com/pi-hole/pi-hole/commit/dac27f1f181f0c107ed623ca17e946fc9aafc045
# Category: 
# Notes: 
# Changed content:
# - net_gateway=$(ip route | grep default | cut -d ' ' -f 3)
# + net_gateway=$(ip route | grep default | cut -d ' ' -f 3 | head -n 1)
################################################################################
# crude regex to match an IPv4 address (crude because it allows numbers larger than 255)
# the problem here is that multiple IPv4 addresses could be returned (and not their field ranges)
# ! not 100% sure this is capable of catching the bug
# ! i tried to annotate that the entire output must be exactly one line containing an IPv4 address
# @output "(([0-9]{1,3}\.){3}[0-9]{1,3}\n){1}"
        net_gateway=$(ip route | grep default | cut -d ' ' -f 3 | head -n 1)