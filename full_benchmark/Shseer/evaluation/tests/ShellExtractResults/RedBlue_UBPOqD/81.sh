#!/bin/sh
USERNAME=$(id -un)
#/opt/jakarta-tomcat-3.2.3/bin/shutdown.sh
#/opt/jakarta-tomcat-4.1.24/bin/shutdown.sh
/var/tmp/$USERNAME/txmud/tomcat6/bin/shutdown.sh

