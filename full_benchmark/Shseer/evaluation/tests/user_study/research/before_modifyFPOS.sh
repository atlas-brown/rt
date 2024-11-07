#!/bin/bash
# Script made to customize FullPageOS on a raspberry Pi

# check if script is root and restart as root if not
[ "$UID" -eq 0 ] || exec sudo bash "$0" "$@"

EditChromiumScript(){
  # Disable default chromium start behaviour and go to error handling method
  echo Editing "/home/pi/scripts/start_chromium_browser"...
  sed -i '6,7s/.*/# &/' /home/pi/scripts/start_chromium_browser

}

SetHostname(){
  # set hostname
  echo
  echo Checking hostname...
  echo Current hostname is $HOSTNAME
  read -r -p "Enter NEW hostname (or <Enter> to continue unchanged): " NEWHOSTNAME
  if [ ! -z $NEWHOSTNAME ] ; then
    hostnamectl set-hostname --static "$NEWHOSTNAME"
  fi
}

EditCrontab(){
  # Edit crontabfile
  CRONTABTMPFILE=/tmp/crontab.tmp

  # Save current crontab
  crontab -l > $CRONTABTMPFILE

  #echo new cron into cron file
  echo "# Reboot RPI nightly
  0 3 * * * sudo reboot now

  # Refresh browser window after 30 minutes
  30 * * * * /home/pi/scripts/refresh
  " >> $CRONTABTMPFILE

  # Replace crontab from tmpfile
  crontab $CRONTABTMPFILE
  rm $CRONTABTMPFILE
}

ChangePassword(){
  echo Changing password:
  passwd pi
}

SetLocale(){
  #localectl set-locale LANG=da_DK.UTF-8
  export LANGUAGE=en_GB.UTF-8
  export LANG=en_GB.UTF-8
  #export LC_ALL=da_DK.UTF-8
  locale-gen da_DK.UTF-8
  #update-locale LANG=da_DK.UTF-8 LANGUAGE
  update-locale LC_TIME=da_DK.UTF-8
  update-locale LC_NUMERIC=da_DK.UTF-8
  #dpkg-reconfigure locales
}

ChangeKeyboard(){
  KBDLANG='da'
  sed -i 's/XKBLAYOUT=\"\w*"/XKBLAYOUT=\"'$KBDLANG'\"/g' /etc/default/keyboard
}

SetTimeZone(){
  timedatectl set-timezone Europe/Copenhagen
}

UpdateOS(){
  apt-get -y update
  apt-get -y upgrade
}

SetFrydensbergViggo(){
    echo 'https://fryd.viggo.dk/screen/1' > /boot/fullpageos.txt
}

PressAnyKeyToContinue(){
    read -n 1 -s -r -p "Press any key to continue..."
}

Restart(){
  echo Rebooting now...
  reboot now
}

# Main
EditChromiumScript
SetHostname
EditCrontab
ChangePassword
SetLocale
ChangeKeyboard
SetTimeZone
UpdateOS
SetFrydensbergViggo
PressAnyKeyToContinue
Restart
