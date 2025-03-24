#!/usr/bin/env bash

################################################################################
# Commit message: Improved regex: Remove all leading points from domain (.....xyz => .xyz). Return not only a part, but fill validated domain
# Commit URL: https://github.com/pi-hole/pi-hole/commit/1bf43b04254559896f5e3a59667a18520401cb78
# Category: 
# Notes: 
# Changed content:
# - echo $* | sed 's/^\.//' | sed "s/[]\\.|$(){}?+*^]/\\\\&/g" | sed "s/\\//\\\\\//g"
# + echo $* | sed 's/^\.*//' | sed "s/[]\.|$(){}?+*^]/\\\\&/g" | sed "s/\\//\\\\\//g"
################################################################################
# @assert "sed 's/^\.//'" --> "[^.].*"
    echo $* | sed 's/^\.//' | sed "s/[]\\.|$(){}?+*^]/\\\\&/g" | sed "s/\\//\\\\\//g"