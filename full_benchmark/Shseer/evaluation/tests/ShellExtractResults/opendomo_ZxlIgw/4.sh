#!/bin/sh
#desc:Install plugin from Github
#type:local
#package:oddevel

# Copyright(c) 2015 OpenDomo Services SL. Licensed under GPL v3 or later

if test -z "$2"
then
	echo "#>Install plugin from Github"
	echo "form:`basename $0`"
	echo "	user	User	text	$1"
	echo "	project	Project	text	$2" 
	echo "#TIP If you have a project created in Github, you just need to enter the project name and your user"
	echo "actions:"
	echo "	goback	Back"
	echo "	installPluginFromGithub.sh	Install"	
else
	echo "#LOADING Installing plugin"
	echo
	if /usr/local/opendomo/bin/plugin_add_from_gh.sh $1 $2 >/dev/null
	then
		echo "#INFO Plugin [$2] installed"
	else
		echo "#ERRO The plugin was not found"
	fi
	/usr/local/opendomo/viewProjects.sh
fi
echo
