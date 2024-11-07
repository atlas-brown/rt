#!/bin/sh

USERNAME=$(id -un)
#CLASSPATH=/usr/local/mysql/mm.mysql-2.0.14-bin.jar
#export CLASSPATH

#/opt/jakarta-tomcat-3.2.3/bin/startup.sh
/var/tmp/$USERNAME/txmud/tomcat6/bin/startup.sh
