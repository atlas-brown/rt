#!/bin/sh
# (C) 2015 Gunnar Andersson
# This file is part of franca_install_automation
# License: See project directory


die() {
   echo Failed - stopping
   exit 1
}

echo Fetching from origin
git fetch origin
for br in $(git branch --list | egrep -v 'master|deprecated=|broken=|experimental' | sed 's/\*//' ) ; do
   [ -n "$br" ] && {
      echo '----------------------------------------------'
      echo "### $br ###"
      echo '----------------------------------------------'
      git checkout $br || die
      echo -n "Merge origin/$br " ; git merge origin/$br
      echo -n "Merge master " ; git merge master -m "Merge master branch"
   }
done

echo Checking out master 
git checkout master

