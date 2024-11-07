#!/bin/sh
#desc:Push changes to GitHub
#package:oddevel
#type:local

# Copyright(c) 2015 OpenDomo Services SL. Licensed under GPL v3 or later

TMPDIR="/var/opendomo/tmp"
AUTHORID="$1"
GITPROJ="$2"
DESCRIPTION="$3"
LOGDIR="/var/opendomo/log"

if test -z "$3"
then
	echo "#> Push changes"
    echo "form:pushChangesToGithub.sh"
	echo "	owner	Owner	text	$1"
	echo "	repo	Repository	text	$2"
	echo "	comments	Comments	text	$3"
    echo
    exit 0
fi


if test -f "/home/$USER/.gitdata"; then
	source "/home/$USER/.gitdata"
else
	echo "#ERR Your Github user account is not yet configured"
	echo 
	/usr/local/opendomo/configureGithub.sh
	exit 0
fi



# First we go to the working directory
cd "$TMPDIR/$GITPROJ"
INFOFILE=`ls var/opendomo/plugins/*.info`

# Find information of the project
source $INFOFILE

# Last: commit changes 
if test -x /usr/bin/git
then
	EMAIL=`cat /home/$USER/.email` 2>/dev/null
	git config --global user.name $USER
	git config --global user.email $EMAIL
	git commit -a -m "$DESCRIPTION"
	if git push https://$USERNAME:$PASSWORD@github.com/$AUTHORID/$REPOSITORY.git master >/dev/null
	then
		echo "#> Push changes"
		echo "form:viewProjects.sh"
		echo "	projectid	projectid	hidden	$GITPROJ"
		echo "#INFO Changes successfully uploaded"
		echo "actions:"
		echo "	viewProjects.sh	Back"
		echo
	fi
else
	echo "#ERROR GIT is not installed"
	exit 1
fi


