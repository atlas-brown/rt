#!/bin/bash
#
# To use:
# - Custom files must be listed under "files_to_port" file.
# - Old version must be in public_html folder.
# - New version must be in moodle folder.
# - Must be run from the parent folder where public_html and moodle lie.
#
# Then all you have to do is run this script and cross your fingers!
#
# migrate.sh [option]
# Options
#   list: enumerate actions
#   <action nbr>: skip up to that action number.
#
# Examples:
#   migrate.sh
#     Runs all actions.
#
#   migrate.sh list
#     List actions.
#
#   migrate.sh 6
#     Skips to action number 5 (updateDb).


dbdir="/var/lib/mysql"
dbbackups="${dbdir}/../mysql_backups"
moodledata="moodledata"
moodle="public_html/moodle"
newmoodle="moodle"
newver=`grep '^[[:space:]]*$release' ${newmoodle}/version.php | cut -d\' -f2 | cut -d\  -f1`
backupsuffix=".preMoodle-$newver"

listFunctions() {
	declare -F | cut -d\  -f3- | sed -n '/^action_/{s/action_//;p}'
}

maintenance() {
	for site in $(siteNameFromConf ../*/moodle_config.php); do
		(
		cd public_html
		export HTTP_HOST=$site
		opt=$1
		shift
		case "$opt" in
			'')
				# Report active (not in maintenance)
				echo "*** Checking $site ..." >&2
				php admin/cli/maintenance.php | fgrep -q disabled && echo $site
				;;
			*)
				# Enable/disable maintenance
				if ! echo " $* " | fgrep -q " $site "; then
					echo "Skipping $opt for $site ..."
					continue
				fi
				ing=${opt^}
				ing=${ing/e/ing}
				echo "*** $ing maintenance for $site ..."
				php admin/cli/maintenance.php --$opt
				;;
		esac
		)
	done
}

action_activateMaintenance() {
	maintenance enable
}

action_backupDb() {
	dbbkpbase=/var/lib/mysql${backupsuffix}
	dbbkp="$dbbkpbase".tgz
	count=0

	service mysql stop || exit 1

	while [ -f "$dbbkp" ]; do
		let count++
		dbbkp="$dbbkpbase"-$(printf "%03d" $count).tgz
	done

	if ! (cd /var/lib;tar czvf $dbbkp ./mysql); then
		echo "Error, aborting."
		exit 1
	fi

	service mysql start || exit 1
}

siteNameFromConf() {
	grep '^ *$CFG->wwwroot' $* | cut -d: -f2- | cut -d/ -f3 | cut -d\' -f1 | cut -d: -f1 | sort -u
}

action_backupSites() {
	for siteConfig in ../*/moodle_config.php; do
		siteDir=$(dirname "$siteConfig")
		site=$(siteNamefromConf "$siteConfig")
	
		echo -e "***\n*** Backing up ${site}\n***"
	
		dbname=`grep '^[[:space:]]*$CFG->dbname' ${siteConfig} | cut -d\' -f2`
		if [ "$dbname" = "" ]
		then
			dbname="moodle"
			echo "Unable to find db name. Using '$dbname'. Press <Enter> to continue."
			read dummy
		fi
	
		(cd "$siteDir"
		pwd
		if [ ! -d "$moodledata" ]
		then
			echo "NOT BACKING UP MOODLEDATA, press <Enter> to continue or ctrl+c to abort."
			read line
		else
			echo "Backing up moodledata..."

			suffixsuffix=""
			backupdata="${moodledata}${backupsuffix}"
			while [ -d "${backupdata}${suffixsuffix}" ]; do
				let "count++"
				suffixsuffix=$(printf "_%04d" $count)
			done

			backupdata="${backupdata}$suffixsuffix"

			if ! cp -rip "$moodledata" "${backupdata}"
			then
				echo "Error, aborting."
				exit 1
			fi
		fi
		)
	done
}

action_customFiles() {
	echo "Generating add-on list..."
	(
		cd ${moodle}
		find . -maxdepth 2 -type d > /tmp/curr.list
	)
	(
		cd ${newmoodle}
		find . -maxdepth 2 -type d > /tmp/new.list
	)
	diff /tmp/curr.list /tmp/new.list | grep "^<" | cut -d\  -f2- > /tmp/diff.list
	
	sort -u files_to_ignore > /tmp/ignore.list
	sort -u /tmp/diff.list > /tmp/diff2.list
	join -o 1.1 -v 1 -1 1 -2 1 /tmp/diff2.list /tmp/ignore.list > /tmp/diff3.list

	cat <<%
Found these add-ons:
$(cat /tmp/diff3.list)
%
	read -p "Press <Enter> to continue" line
	
	echo "Copying custom add-ons and files to new version..."
	cat files_to_port >> /tmp/diff3.list
	
	#set -xv
	exec 3<&0 < /tmp/diff3.list
	while read file
	do
		dest=`dirname "$file" | sed "s,^,${newmoodle}/,"`
		fname=`basename "$file"`
		cp -ri "${moodle}/$file" "$dest"/. <&3 && echo "$file"
		ls -ld "$dest"/"$fname"
	done
	exec <&3 3<&-
}

action_replaceOld() {
	echo "Replacing old version with new..."
	read -p "Press <Enter> to continue" line
	
	chown -R www-data:www-data "${newmoodle}"

	suffixsuffix=""
	backupbin="${moodle}${backupsuffix}"
	while [ -d "${backupbin}$suffixsuffix" ]; do
		let count++
		suffixsuffix=$(printf "%03d" $count)
	done
	backupbin="${backupbin}$suffixsuffix"

	if ! mv -i "${moodle}" "${backupbin}"
	then
		echo "Error, aborting."
		exit 1
	fi
	
	mv "${newmoodle}" "${moodle}"
}

action_updateDatabases() {
	for site in $(siteNameFromConf ../*/moodle_config.php); do
		echo -e "***\n*** Updating $site\n***"
		sudo -u www-data HTTP_HOST=$site php ./public_html/admin/cli/upgrade.php --non-interactive
	done
}

action_zReopenSites() {
	echo "*** Reopen sites:" $activeSites

	maintenance disable $activeSites
}

skip=0
count=1
if [ "$1" = "list" ]; then
	echo -e "***\n*** Listing functions:"
	for func in $(listFunctions); do
		echo "*** $((count++)): $func"
	done
	echo "***"
	exit 0
fi

if [ "$1" != "" ]; then
	skip=$1
fi

if [ "$skip" -lt "5" ]; then
	for i in 1 2
	do
		if [ ! -r "${moodle}" ]
		then
			echo "Unable to find '${moodle}'"
			moodle=`dirname "$moodle"`
		fi
	done
	
	if [ "${moodle}" = "." ]
	then
		echo "\$moodle is '.', Unable to continue..."
		exit 1
	else
		echo "Moodle is $moodle"
	fi
	
	if [ ${#newver} -eq 0 ]
	then
		echo "Aborting. Couldn't find newver. Is the new 'moodle' here?"
		exit 1
	fi

	echo "New version: '$newver'"
	echo "Press <Enter> to confirm, or ctrl+c to abort"
	read line
fi

export activeSites=$(maintenance)

echo "*** Active sites:" $activeSites

for func in $(listFunctions); do
	if [ $count -lt $skip ]; then
		echo "Skipping $func (step $count)..."
	else
		echo "Will call $func"
		read -p "Press <Enter> to continue" line
		action_$func
	fi
	let "count++"
done

maintenance disable $activeSites
