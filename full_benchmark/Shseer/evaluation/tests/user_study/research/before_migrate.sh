#!/bin/bash
#
# To use:
# - Custom files must be listed under "files_to_port" file.
# - Old version must be in public_html folder.
# - New version must be in moodle folder.
# - Must be run from the parent folder where public_html and moodle lies.
#
# Then all you have to do is run this script and cross your fingers!
#

dbdir="/var/lib/mysql"
dbbackups="${dbdir}/../mysql_backups"
moodledata="moodledata"
moodle="public_html/moodle"
newmoodle="moodle"
newver=`grep '^[[:space:]]*$release' ${newmoodle}/version.php | cut -d\' -f2 | cut -d\  -f1`
backupsuffix=".preMoodle-$newver"

backupDb() {
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

backupSites() {
	for siteConfig in ../*/moodle_config.php; do
		siteDir=$(dirname "$siteConfig")
		site=$(basename "$siteDir")
	
		echo -e "***\n*** Backing up ${site}\n***"
	
		dbname=`grep '^[[:space:]]*$CFG->dbname' ${siteConfig} | cut -d\' -f2`
		if [ "$dbname" = "" ]
		then
			dbname="moodle"
			echo "Unable to find db name. Using '$dbname'. Press <Enter> to continue."
			read dummy
		fi
	
		if [ 0 -eq 1 ]
		then
		echo "Backing up database..."

		count=0
		suffixsuffix=""
		while [ -d "$dbdir"/"${dbname}${backupsuffix}${suffixsuffix}" ]; do
			let "count++"
			suffixsuffix=$(printf "_%04d" $count)
		done

		backupsuffix=${backupsuffix}${suffixsuffix}

		if ! cp -rip "$dbdir"/"$dbname" "$dbbackups"/"${dbname}$backupsuffix"
		then
			echo "Error, aborting."
			exit 1
		fi
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

customFiles() {
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

replaceOld() {
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

updateDatabases() {
	for site in $(grep '^ *$CFG->wwwroot' ../*/moodle_config.php | cut -d: -f2- | cut -d/ -f3 | cut -d\' -f1 | sort -u); do
		echo -e "***\n*** Updating $site\n***"
		sudo -u www-data HTTP_HOST=$site php ./public_html/admin/cli/upgrade.php --non-interactive
	done
}

skip=0
count=1
if [ "$1" = "list" ]; then
	echo -e "***\n*** Listing functions:"
	for func in $( declare -F | cut -d\  -f3-); do
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

for func in $(declare -F| cut -d\  -f3-); do
	if [ $count -lt $skip ]; then
		echo "Skipping $func (step $count)..."
	else
		echo "Will call $func"
		read -p "Press <Enter> to continue" line
		$func
	fi
	let "count++"
done


