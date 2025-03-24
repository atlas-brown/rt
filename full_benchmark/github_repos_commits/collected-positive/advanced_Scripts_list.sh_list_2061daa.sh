#!/usr/bin/env bash
################################################################################
# Commit message: Don't forget to escape also the slash "/"
# Commit URL: https://github.com/pi-hole/pi-hole/commit/2061daa902f9dc0f56daccfb024eeaca3ea1398d
# Category: 
# Notes: 
# Changed content:
# - echo $* | sed "s/[]\\.|$(){}?+*^]/\\\\&/g"
# + echo $* | sed "s/[]\\.|$(){}?+*^]/\\\\&/g" | sed "s/\\//\\\\\//g"
################################################################################
# match . \ / | [ ] $ ( ) { } ? + * ^ only if they are escaped (e.g match \. but not ., match \? but not ?)
# @output "(\\\.|\\\\|\\\/|\\\||\\\[|\\\]|\\\$|\\\(|\\\)|\\\{|\\\}|\\\?|\\\+|\\\*|\\\^|[^\.\/\|\[\]\$\(\)\{\}\?\+\*\^\\])*"
    echo $* | sed "s/[\]\\.|$(){}?+*^]/\\\\&/g"