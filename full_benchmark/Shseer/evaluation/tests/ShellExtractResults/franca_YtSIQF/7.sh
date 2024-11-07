#!/bin/sh
# (C) 2015 Gunnar Andersson
# This file is part of franca_install_automation
# License: See project directory

die() {
   echo Failed - stopping
   [ -n "$*" ] && echo "Message: $*"
   exit 1
}

cd "$(dirname $0)"
[ -x ./tag.sh ] || die "Can't find executable tag.sh in this directory"

echo "Warning - this will tag all branches - hit return x 2 to continue, or CTRL-C now!"
read
read

for b in debian_7.3-lxde trusty64-lxde trusty64-unity ; do
   git checkout $b && ./tag.sh
done

echo Checking out master 
git checkout master

