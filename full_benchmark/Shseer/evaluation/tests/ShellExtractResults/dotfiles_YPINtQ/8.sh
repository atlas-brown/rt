#!/bin/sh

# Restart ADB Server
alias adb_restart='adb kill-server; adb start-server; adb devices; adb devices'

# Take Screenshot
#
# Usage: adb_screenshot > image.png
alias adb_screenshot="adb shell screencap -p | perl -pe 's/\x0D\x0A/\x0A/g'"
