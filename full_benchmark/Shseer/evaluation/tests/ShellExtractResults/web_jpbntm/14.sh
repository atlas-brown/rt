#!/bin/sh

# /etc/X11/xinit/xinitrc
#
# global xinitrc file, used by all X sessions started by xinit (startx)

# invoke global X session script
. /etc/X11/Xsession
xset dpms 0 0 0
xset -dpms
xset s off
xset s noblank
unclutter -idle 0.01 -root &
