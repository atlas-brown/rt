#!/bin/sh
#desc:View projects
#package:oddevel

# Copyright(c) 2015 OpenDomo Services SL. Licensed under GPL v3 or later

## This service will let the developer choose which projects are available.
##
## In order to import the development version of an installed plugin, is 
## necessary to have all the requested variables in the info file. These
## variables are AUTHORID and REPOSITORY.

DEVELDIR="/var/opendomo/tmp"

if test -z "$1"; then
	echo "#>Development plugins installed"
	echo "list:viewProjects.sh	detailed"
	cd $DEVELDIR
	for project in *; do
		if test -d "$project" && test -f ./$project/build.bat
		then
			found=1
			echo "	-$project	$project 	project"
		fi
	done
	if test -z "$found"; then
		echo "#INFO No projects were found"
	fi
	echo "actions:"
	echo "	installPluginFromGithub.sh	Add new plugin"
	echo
	echo "#>Get development version"
	echo "list:viewProjects.sh	detailed"
	cd /var/opendomo/plugins
	for project in *.info; do
		REPOSITORY=""
		AUTHORID=""
		DESCRIPTION=""
		CODE=`echo $project | cut -f1 -d.`
		source ./$project
		if test -z "$AUTHORID" || test -z "$REPOSITORY"; then
			echo "	-	$CODE	project invalid	Missing parameters in info file"
		else
			if test -d $DEVELDIR/$REPOSITORY; then
				echo "	-$REPOSITORY	$CODE 	project selected	$DESCRIPTION"
			else
				echo "	-$AUTHORID:$REPOSITORY	$CODE 	project 	$DESCRIPTION"
			fi
		fi
	done
else
	PROJECT="$1"
	if ! test -d $DEVELDIR/$PROJECT
	then
		AUTHORID=`echo $1 | cut -f1 -d:`
		REPOSITORY=`echo $1 | cut -f2 -d:`
		echo "#>Install plugin from Github"
		echo "form:installPluginFromGithub.sh"
		echo "	user	User	text	$AUTHORID"
		echo "	project	Project	text	$REPOSITORY" 
		echo "actions:"
		echo "	goback	Back"
		echo "	installPluginFromGithub.sh	Install"		
		#echo "#LOADING Installing plugin"
		#echo

		#/usr/local/opendomo/installPluginFromGithub.sh $AUTHORID $REPOSITORY >/dev/null
		#PROJECT="$REPOSITORY"
		exit 0
	fi

	echo "#>Details"
	echo "form:viewProjects.sh"	
	cd $DEVELDIR/$PROJECT
	INFOFILE=`ls ./var/opendomo/plugins/*.info`
	CODENAME=`basename $INFOFILE | cut -f1 -d.`
	DEPENDENCES=`cat ./var/opendomo/plugins/$CODENAME.deps` 
	source $INFOFILE
	echo "	owner	owner	hidden	$AUTHORID"
	echo "	dir 	Directory	hidden	$PROJECT"
	echo "	desc	Description	readonly	$DESCRIPTION"
	echo "	auth	Author	readonly	$AUTHOR"
	echo "	deps	Dependences 	readonly	$DEPENDENCES"
	echo "actions:"
	echo "	goback	Back"
	echo "	installPluginFromGithub.sh	Update"
	echo "	removeDevelopmentProject.sh	Remove"
	echo "	pushChangesToGithub.sh	Push changes"
	echo
	cd $DEVELDIR
	echo "#> Services"
	echo "list:editFile.sh	detailed foldable"
	for serv in `find ./$PROJECT/usr/local/opendomo/services -type f`; do
		desc=`head $serv -n4 | grep desc: | cut -f2 -d:`
		package=`head $serv -n4 | grep package: | cut -f2 -d:`
		bname=`basename $serv`
		if test -z "$desc" ||  test -z "$package"
		then
			echo "	-$serv	$bname	service invalid	$desc"
		else
			echo "	-$serv	$bname	service	$desc"
		fi
		
	done
	echo
	
	echo "#> Daemons"
	echo "list:editFile.sh	detailed foldable"
	for serv in `find ./$PROJECT/usr/local/opendomo/daemons -type f`; do
		desc=`head $serv -n4 | grep Short-Description | cut -f2 -d:`
		bname=`basename $serv`
		if grep -q start $serv && grep -q stop $serv && grep -q status $serv 
		then
			echo "	-$serv	$bname	daemon	$desc"
		else
			echo "	-$serv	$bname	daemon invalid	$desc"
		fi
	done
	echo
	
	echo "#> Other files"
	echo "list:editFile.sh	detailed foldable"
	for serv in `find ./$PROJECT/var/www -type f`; do
		extension=${serv##*.}
		bname=`basename $serv`
		echo "	-$serv	$bname	$extension file	$extension"
	done
fi
echo
