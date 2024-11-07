#!/bin/bash

#### ABOUT
#
# This script is meant to be used as a LaunchDaemon that runs daily on a Jamf Pro-managed Mac.
#
# Stores the age of restart-required updates in plist
#
# Nags user daily when there are updates that require restart
# 
# When the maximum update age is reached as defined in VARIABLES below, the user is notified and updates are forced
#
# Accounts for system downtime by advancing day counter by number of days of downtime
#
# Desired upgrade: nag every 60 minutes on final day
#
#####

##### VARIABLES

# Maximum age of restart-required updates (in days) before updates and restart are forced.
maxUpdateAge="14"
# Derive final day from above
((finalday=maxUpdateAge-1))

# Absolute path to local plist for config & management data
localDataPlist="/Library/myOrg/Data/com.myOrg.jamfLocalExtensionAttributes.plist"
# Path without filename derived from above localDataPlist value
localDataPlistPath=$( dirname "$localDataPlist" )

# Are there updates that require restart today? 0=no nonzero=yes
areThereUpdatesThatRequireRestartToday=$( /usr/sbin/softwareupdate -l | /usr/bin/grep -ic "restart" )

##### PREP

# Make localDataPlist if it doesn't exist.
if [ ! -e "$localDataPlist" ]; then
  mkdir -p "$localDataPlistPath"
  echo '<?xml version="1.0" encoding="UTF-8"?>'  >> "$localDataPlist"
  echo '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">' >> "$localDataPlist"
  echo '<plist version="1.0">' >> "$localDataPlist"
  echo "<dict>" >> "$localDataPlist"
  echo '</dict>' >> "$localDataPlist"
  echo '</plist>' >> "$localDataPlist"
fi

# Make daysRestartHasBeenRequired key with integer type and 0 value if it doesn't exist
/usr/libexec/PlistBuddy -c "Print :software:macOS:softwareUpdates:daysRestartHasBeenRequired" "$localDataPlist"
if [ "$?" -ne 0 ]; then
  /usr/libexec/PlistBuddy -c "Add :software:macOS:softwareUpdates:daysRestartHasBeenRequired integer 0" "$localDataPlist"
fi

# Get current value of daysRestartHasBeenRequired
daysRestartHasBeenRequired=$( /usr/libexec/PlistBuddy -c "Print :software:macOS:softwareUpdates:daysRestartHasBeenRequired" "$localDataPlist" )

# Get days since $localDataPlist was modified
plistModDate=$(date -r "$localDataPlist" +%s)
todaysSincePlistModDate=$(date +%s)          
daysSincePlistMod=$(expr \( $todaysSincePlistModDate - $plistModDate \) / 86400)

##### WORK

# Update $daysRestartHasBeenRequired by $daysSincePlistMod to account for system downtime
if [ "$daysSincePlistMod" -gt 0 ]; then
	((daysRestartHasBeenRequired=daysRestartHasBeenRequired+daysSincePlistMod))
fi

# Increment (if restart required) or reset (if not) daysRestartHasBeenRequired in plist
if [ "$areThereUpdatesThatRequireRestartToday" -ne 0 ]; then
  ((daysRestartHasBeenRequired++))
  /usr/libexec/PlistBuddy -c "Set :software:macOS:softwareUpdates:daysRestartHasBeenRequired $daysRestartHasBeenRequired" "$localDataPlist"
else
  /usr/libexec/PlistBuddy -c "Set :software:macOS:softwareUpdates:daysRestartHasBeenRequired 0" "$localDataPlist"
fi

# Notify and/or update
if [ "$daysRestartHasBeenRequired" -eq 0 ]; then
	exit 0
elif [ "$daysRestartHasBeenRequired" -gt 0 ] && [ "$daysRestartHasBeenRequired" -lt "$maxUpdateAge" ]; then
  /Library/Application\ Support/JAMF/bin/Management\ Action.app/Contents/MacOS/Management\ Action -title 'Apple Updates Required' -subtitle "Uninstalled patches are $daysRestartHasBeenRequired day(s) old" -message 'Update in Self Service or App Store.'
else
  /Library/Application\ Support/JAMF/bin/Management\ Action.app/Contents/MacOS/Management\ Action -title 'Apple Updates Required' -subtitle "Uninstalled patches are > $maxUpdateAge days old" -message 'Update & restart will begin now.'
  jamf policy -event installAppleUpdatesAndRestartNow
fi

exit 0
