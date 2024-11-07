#!/bin/bash

##### FUNCTIONS #####
fUpdateEverything ()
{

    ## Once the user OKs the updates or they run automatically, reset the timer to 4 
    echo "4" > /Library/myOrganization/.SoftwareUpdateTimer.txt

	/usr/local/bin/jamf policy -event swurestart

}

##### VARIABLES #####
## Set up the software update time if it does not exist already
if [ ! -e /Library/myOrganization/.SoftwareUpdateTimer.txt ]; then
	mkdir /Library/myOrganization
    echo "4" > /Library/myOrganization/.SoftwareUpdateTimer.txt
fi

## Get the timer value
Timer=`cat /Library/myOrganization/.SoftwareUpdateTimer.txt`

#see if user logged in
USER=`/usr/bin/who | /usr/bin/grep console | /usr/bin/cut -d " " -f 1`;

# Is Do Not Disturb enabled? 1=Y, 0=N
DnD=`defaults -currentHost read ~/Library/Preferences/ByHost/com.apple.notificationcenterui doNotDisturb`

# Do any needed updates require a reboot?
/usr/sbin/softwareupdate -l | /usr/bin/grep -i "restart"
if [[ `/bin/echo "$?"` == 0 ]]
	then
		rebootRequired="Y"
	else
		rebootRequired="N"
fi


##### SCRIPT #####

# If there is no user logged in, update everything.
if [ -z "$USER" ] 
	then
		fUpdateEverything
fi

# If no available updates require reboot install the updates
if [[ "$rebootRequired" == "N" ]]
	then
		/usr/local/bin/jamf policy -event swunorestart
fi

# If someone one is logged in and Do not disturb is off, present deferment options.
if [ -n "$USER" ] && [ "$DnD" == 0 ] && [ "$rebootRequired" == "Y" ]
	then
		if [ "$Timer" -ne "0" ] #timer is not done
			then
				OKTORESTART=`/Library/Application\ Support/JAMF/bin/jamfHelper.app/Contents/MacOS/jamfHelper -startlaunchd -windowType utility -icon /System/Library/CoreServices/Software\ Update.app/Contents/Resources/SoftwareUpdate.icns -heading "Software Updates are Available" -description "This Mac must install Apple updates that require a restart. You may defer the update $Timer more times. Would you like to install the udpates now?" -button1 "Install" -button2 "Defer" -cancelButton "2" -defaultButton "1"`
					if [ "$OKTORESTART" == "0" ]
						then
							fUpdateEverything
						else
							echo "User deferred update"
							newTimer=$((Timer-1))
							echo "$newTimer" > /Library/myOrganization/.SoftwareUpdateTimer.txt
					fi
			else
				/Library/Application\ Support/JAMF/bin/jamfHelper.app/Contents/MacOS/jamfHelper -windowType utility -icon /System/Library/CoreServices/Software\ Update.app/Contents/Resources/SoftwareUpdate.icns -heading "Software Updates will Install" -description "This Mac must install Apple updates that require a restart. The deferral limit has been exhausted. These updates will install now, followed by an automatic restart." -timeout 30
				fUpdateEverything
		fi
fi
  
exit 0

##### Future Enhancements

## Read size of updates and current network speed to Apple and calculate approximate time

## Fix time/times plural issue in deferment message.
