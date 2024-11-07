#!/bin/bash

#-----------------------------------------------------------
#
# Quit: quits Mac OS X applications politely
#
# Written by Jon Stovell, July 11, 2009
#
#-----------------------------------------------------------

#-----------------------------------------------------------
# This script takes one or more application names as
# arguments, and uses osascript to tell each one to quit.
# Unlike kill and killall, this allows applications to save
# files and perform any necessary operations before exiting.
#
# This script is not case sensitive.
#
# Note: application names are NOT process names! The
# application name is the name that Script Editor uses.
# Often the process name and the application name are
# identical, but not always.
#-----------------------------------------------------------

usage()
{
	echo "Usage: `basename $0` [-a] [-p] Application1 \"Application 2\" ..."
	echo ""
	echo "Arguments are the names of one or more applications."
	echo "Arguments are not case sensitive."
	echo "Arguments with spaces should be quoted."
	echo ""
	echo "Options:"
	echo "	-a	Match argument string with any of the application's"
	echo "		name, short name, title, or display name."
	echo "		E.g.: \`quit \"Microsoft Word\"\` and \`quit -a Word\`"
	echo "		will both quit Microsoft Word, because the app calls"
	echo "		itself \"Word\" in the menu bar."
	echo "	-p	Use partial matches (e.g. edit for TextEdit). Prompts"
	echo "		for confirmation."
	echo ""
	exit 65
}

searchall=1
is_contains="is"
while getopts "ap" opt
do
	case $opt in
	a) searchall=0 ;;
	p) is_contains="contains" ;;
	[?]) usage; exit ;;
	esac

	shift $(($OPTIND - 1)) # Decrements the argument pointer so it points to next argument. $1 now references the first non option item supplied on the command-line if one exists.
done

if [ -z $1 ]; then usage; fi

for arg in "$@"
do
	if [ searchall=0 ]
	then
		appname=`osascript -e "tell application \"System Events\" to return every application process whose (name $is_contains \"$arg\" or short name $is_contains \"$arg\" or title $is_contains \"$arg\" or displayed name $is_contains \"$arg\")"`
	else
		appname=`osascript -e "tell application \"System Events\" to return every application process whose name $is_contains \"$arg\""`
	fi

	if [[ -n $appname && $appname != *", "* ]] # found 1 matching application
	then
		if [[ $is_contains == is ]]
		then
			osascript -e "ignoring application responses" -e "tell application \"$appname\" to quit with saving" -e "end ignoring"
		else
			echo "Choose the application to quit:"

			eval set $appname # this allows multi-word selections in select
			select appname in "$@"
			do
				osascript -e "ignoring application responses" -e "tell application \"$appname\" to quit with saving" -e "end ignoring"
				break
			done
		fi

	elif [[ -z $appname ]] # found no matching application
	then
		echo "No running application matches \"$arg\""

	elif [[ $appname == *", "* ]] # found >1 matching applications.
	then
		appname=`echo $appname | sed -e 's/^/\"/' -e 's/$/\"/' -e 's/, /\" \"/'`
		echo "\"$arg\" matches multiple applications."
		echo "Choose the application to quit:"

		eval set $appname # this allows multi-word selections in select
		select appname in "$@"
		do
			osascript -e "ignoring application responses" -e "tell application \"$appname\" to quit with saving" -e "end ignoring"
			break
		done
	fi
done
