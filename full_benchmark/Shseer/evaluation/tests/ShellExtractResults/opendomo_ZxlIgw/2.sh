#!/bin/sh
#desc:Add plugin from GitHub
#package:oddevel
#type:local

# Copyright(c) 2015 OpenDomo Services SL. Licensed under GPL v3 or later

if test -z "$1"
then
    echo "usage: $0 GITuser GITproject"
	echo "usage: $0 GITuser:GITproject"
    echo
    exit 1
fi

if test -n "$2"
then
	GITUSER="$1"
	GITPROJ="$2"
else
	GITUSER=`echo $1 | cut -f1 -d:`
	GITPROJ=`echo $1 | cut -f2 -d:`
fi

LOGDIR="/var/opendomo/log"
URLPROJ="https://github.com/$GITUSER/$GITPROJ"
CLONEPROJ="https://github.com/$GITUSER/$GITPROJ.git"

# cd 
# TMPDIR=`pwd` # So far we don't have much space in the home dir. 

TMPDIR="/var/opendomo/tmp"
cd "$TMPDIR"
if wget --no-check-certificate -qO- "$URLPROJ" &>/dev/null
then
	URLFILE="https://github.com/$GITUSER/$GITPROJ/tarball/master"
	echo "# Retrieving file $URLFILE"
else
	echo "#ERROR invalid project $URLPROJ"
	exit 2
fi

# If GIT is installed, it's our first option
if test -x /usr/bin/git
then
	if test -d $GITPROJ
	then
		cd $GITPROJ
		git pull
	else
		git clone $CLONEPROJ
		cd $GITPROJ
	fi
else
	echo "Using direct download. Install git if you want to commit changes"
	rm -fr $TMPDIR/$GITUSER-$GITPROJ-*
	if ! wget --no-check-certificate -q "$URLFILE" -O $TMPDIR/$GITPROJ.tar.gz
	then
		echo "#ERROR downloading file $URLFILE"
		exit 1
	fi

	cd $TMPDIR
	tar -zxf $GITPROJ.tar.gz
	cd $GITUSER-$GITPROJ-*
fi



echo
echo "   ##########################################################################"
echo "   ##   WARNING: you are installing a plugin from the development branch.  ##"
echo "   ##   This means that  the code might be unstable,  so it shouldn't be   ##" 
echo "   ##   used in production environments. Use it AT YOUR OWN RISK!          ##"
echo "   ##########################################################################"
echo 

if ! test -f mkpkg.sh
then
	echo "#ERROR mkpkg.sh script is missing!"
	exit 3
else
	if ! test -x mkpkg.sh
	then
		echo "#ERROR mkpkg.sh script doesn't have execution privileges!"
		exit 3
	fi
fi

if ! test -f build.bat
then
	echo "#ERROR build.bat script is missing!"
	exit 3
fi

if ! test -d usr
then
	echo "#ERROR usr directory is missing!"
	exit 4
fi
if ! test -d var
then
	echo "#ERROR var directory is missing!"
	exit 5
fi	

# Looking for use of undeclared events
EVENTS=`grep -R -e "logevent" usr/local/opendomo/* | sed -e 's/\t//g' -e 's/ /+/g'`
for ev in $EVENTS
do
	SCRIPTNAME=`echo $ev | cut -f1 -d:`
	SCRIPTNAME=`basename $SCRIPTNAME`
	EVENTNAME=`echo $ev | sed -e 's/+/ /g' -e 's/"//g' | awk -F"logevent" '{print $2}' | awk '{print $2 "-" $1}' `
	if ! test -z "$EVENTNAME"; then
		if ! test -f usr/local/opendomo/events/$EVENTNAME
		then
			echo "#WARNING Event $EVENTNAME invoked in $SCRIPTNAME but not defined"
		fi
	fi
done

# Generating automatic doc pages
if test -d usr/local/opendomo/docs; then
	for serv in usr/local/opendomo/services/*/*.sh 
	do
		bname=`basename $serv | cut -f1 -d.`
		grep '##' $serv | sed 's/##//' > usr/local/opendomo/docs/$bname.txt
	done
else
	echo "#WARNING usr/local/opendomo/docs directory does not exist"
fi

# Cleanup old packages
rm *.tar.gz 2> /dev/null
. ./mkpkg.sh >> $LOGDIR/$GITPROJ.log
if test -z "$PKGID"
then
	echo "#ERROR PKGID is not specified!"
	exit 5
fi

# Checking for package information files
if ! test -f var/opendomo/plugins/$PKGID.deps
then
	echo "#ERROR: $PKGID.deps file must exist (may be empty if no dependences required)"
	exit 6
fi
if ! test -f var/opendomo/plugins/$PKGID.info
then
	echo "#ERROR: $PKGID.info file must exist"
	exit 6
else
	source ./var/opendomo/plugins/$PKGID.info
	if test -z "$DESCRIPTION" || test -z "$VERSION" || test -z "$AUTHORID" || test -z "$REPOSITORY"
	then
		echo "#ERROR: Missing required fields in $PKGID.info file"
		echo "DESCRIPTION, VERSION, AUTHORID and REPOSITORY are compulsory"
		exit 7
	fi
fi


# Filesystem testing finished. Now installing package
TGZFILE=`ls *.tar.gz`
echo "# Installing $PKGID ... "
if test -z "$TGZFILE"
then
	echo "#ERROR Plugin tar.gz file was not created"
	exit 6
fi

TGZFILE="`pwd`/$TGZFILE"
echo > $TMPDIR/$GITPROJ.files 
cd /
if tar  --no-overwrite-dir -zxvf $TGZFILE  >> /var/opendomo/plugins/$PKGID.files 
then
	echo "99999999" > /var/opendomo/plugins/$PKGID.version
	#sudo manage_conf.sh copy
	
	createwrappers.sh
	DEPS=`cat /var/opendomo/plugins/$PKGID.deps` 
	if ! test -z "$DEPS"
	then
		echo "# Installing dependences: $DEPS"
		echo $DEPS >> /var/opendomo/apt/queue
		echo "0" > /var/opendomo/apt/update
	fi
	echo "# Plugin $PKGID installed successfully"
else
	echo "#ERROR decompressing file"
	exit 7
fi

