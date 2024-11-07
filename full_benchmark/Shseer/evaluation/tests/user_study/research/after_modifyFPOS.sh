#!/bin/bash
# Script made to customize FullPageOS on a raspberry Pi

# check if script is root and restart as root if not
[ "$UID" -eq 0 ] || exec sudo bash "$0" "$@"

UnpackingFiles(){
  echo Unpacking and moving files from github repository...
  mv /tmp/FullPageOSMods-master/scripts/* /home/pi/scripts
}

EditChromiumScript(){
  # Disable default chromium start behaviour and go to error handling method
  echo Editing "/home/pi/scripts/start_chromium_browser"...
  sed -i '6,7s/.*/# &/' /home/pi/scripts/start_chromium_browser

}

WriteIDfile(){
  read -r -p "Enter name of the Pi: " IDNAME
  if [ ! -z $IDNAME ] ; then
     touch "/home/pi/$IDNAME.id"
  fi
}

SetHostname(){
  # set hostname
  echo
  echo Checking hostname...
  echo Current hostname is $HOSTNAME
  read -r -p "Enter NEW hostname (or <Enter> to continue unchanged): " NEWHOSTNAME
  if [ ! -z $NEWHOSTNAME ] ; then
    hostnamectl set-hostname --static "$NEWHOSTNAME"
    rm -rf ~/.config/chromium/Singleton*
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

# Refresh browser after reboot to avoid start loading delay errors
@reboot sleep 15 && /home/pi/scripts/refresh
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
  sed -i 's/# da_DK.UTF-8 UTF-8/da_DK.UTF-8 UTF-8/' /etc/locale.gen 
  locale-gen
  update-locale LANG=da_DK.UTF-8 LANGUAGE
  #update-locale LC_TIME=da_DK.UTF-8
  #update-locale LC_NUMERIC=da_DK.UTF-8
  #dpkg-reconfigure locales
}

ChangeKeyboard(){
  KBDLANG='da'
  sed -i 's/XKBLAYOUT=\"\w*"/XKBLAYOUT=\"'$KBDLANG'\"/g' /etc/default/keyboard
}

SetTimeZone(){
  echo Setting Timezone...
  timedatectl set-timezone Europe/Copenhagen
}

UpdateOS(){
  apt-get -y update
  apt-get -y upgrade
}

SetCustomStartPage(){
    echo Setting custom FullPageOS startpage
    echo 'https://fryd.viggo.dk/screen/1' > /boot/fullpageos.txt
}

SetDefaultStartPage(){
    echo Setting default FullPageOS startpage
    echo 'http://localhost/FullPageDashboard' > /boot/fullpageos.txt
}

SetCustomSplashscreen(){
  echo Setting custom splash screen...
  CUSTOMSPLASH=/tmp/FullPageOSMods-master/media/custom.png
  [ -f $CUSTOMSPLASH ] && mv /boot/splash.png /boot/splash.png.bak && cp /tmp/FullPageOSMods-master/media/custom.png /boot/splash.png
}

FixError(){
  # This error is due to a mistake in source with the use of sed
  # (Line 22 in https://github.com/guysoft/FullPageOS/blob/devel/src/modules/fullpageos/start_chroot_script)
  echo Fixing errors in /boot/cmdline.txt
  sed -i 's/co logo.nologo consoleblank=0 loglevel=0sole=/logo.nologo consoleblank=0 loglevel=0 quiet console=/' /boot/cmdline.txt

}

PressAnyKeyToContinue(){
    read -n 1 -s -r -p "Press any key to continue..."
    echo
}

Restart(){
  echo Rebooting now...
  reboot now
}

# Main
clear
UnpackingFiles
EditChromiumScript
WriteIDfile    #SetHostname
EditCrontab
ChangePassword
SetLocale
ChangeKeyboard
SetTimeZone
UpdateOS
SetDefaultStartPage  #SetCustomStartPage
SetCustomSplashscreen
FixError
PressAnyKeyToContinue
Restart
