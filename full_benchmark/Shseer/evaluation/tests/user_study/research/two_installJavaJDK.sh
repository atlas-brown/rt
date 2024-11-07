#!/bin/bash

# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
#
# MIT License
# 
# Copyright (c) 2018 Jose Henriquez [https://github.com/jhenriquez418/linux-java-jdk-installer]
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  

# enumerator values to determine the current JDK configuration status...
readonly NOT_INSTALLED=0
readonly INSTALLED_BY_SCRIPT=1
readonly INSTALLED_NOT_CONFIGURED=2
readonly INSTALLED_POINTS_TO_ANOTHER_JDK=3

readonly SCRIPT_VERSION="1.1.0"

# Global variables...
currentJDKStatus=-1
jdkInstalledVersion=""
jdkVersionToInstall=""
systemJavaDir="/usr/lib/jvm"

isOpenJDK=true
processorType=$(getconf LONG_BIT)
jdkExtractedDir=""


# Assign parameters... 
# $1 = JDK file
# $2 = sha256sum value
sourceFile=$1
sha256sum=$2


# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
# Validate we have the correct params...
# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
validateParams() 
{
	if [[ -z $sourceFile && -z $sha256sum ]] || [[ "${sourceFile,,}" = "-h" ]] || [[ "${sourceFile,,}" = "-help" ]] ; then
		# Print help...
		echo ""
		echo "Installs the provided the JDK.  It confirms the tar SHA256 sum matches that of the provided value and performs simple validation to verify the provided tar contains a JDK folder.  Script can intall either an Oracle or Oracle provided OpenJDK 9 or greater.  Installation script has been tested on Ubuntu.  Go to project home page (https://github.com/jhenriquez418/linux-java-jdk-installer) for further info."
		echo ""
		echo "Script must be executed with sudo.  For example:"
		echo ""
		echo "sudo ./installJavaJDK jdk-10_linux-x64_bin.tar.gz 0b14aaecd5323457bd15dc7798d08181ad04bad4156e55387ed714190912a9ce"
		echo ""
		echo "installJavaJDK version $SCRIPT_VERSION"
		echo "Copyright (c) 2018 Jose Henriquez [https://github.com/jhenriquez418/linux-java-jdk-installer]"
		echo "MIT License"
		echo ""
		echo 'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.'
		echo ""
		exit
	fi
		
	echo "*-*-*-*-*           Validating script parameters             *-*-*-*-*"
	echo ""

	# Verify the running user is root!
	if [ $USER != "root" ]; then
		echo "You must run installation script with root.  Validation failed!  Process will end."
		exit
	fi

	# Confirm the user provided the JDK file name to process...
	if [ -z $sourceFile ]; then 
		echo "You must provide a JDK tar file to work with.  Validation failed!  Process will end."
		exit
	fi 

	# Confirm the user provided the sha256sum value for the passed JDK...
	if [ -z $sha256sum ]; then
		echo "You must provide the SHA256 value for the specified JDK.  Validation failed!  Process will end."
		exit
	fi

	# Identify what JDK version we're installing, Oracle or JDK...
	if [ ${sourceFile:0:4} = "jdk-" ]; then
		isOpenJDK=false
		echo "Source file is an Oracle JDK...."
	else
		if [ ${sourceFile:0:8} = "openjdk-" ]; then
			echo "Source file is an OpenJDK..."
		else
			echo "Unknown JDK source!  Program will exit!"
			exit
		fi
	fi

	# Verify the specified parameter file exists...
	if [ ! -e "$sourceFile" ]; then
		echo "Source file [$sourceFile] does not exist in the current directory.  Validation failed!  Process will end."
		exit
	fi
	echo "Specified source file [$sourceFile] exists in current processing directory!"

	# Compare sha256 value...
	shaSUM=$(sha256sum $sourceFile)
	shaSumValue=${shaSUM:0:64}
	shaSumFile=${shaSUM:66}
	echo "Validating SHA256 value..."
	if [ "$sha256sum" != "$shaSumValue" ]; then
		echo "Provided SHA sum value does not match the SHA value for the provided JDK file.  Validation failed!  Process will end."
		exit
	elif [ "$sourceFile" != "$shaSumFile" ]; then
		echo "SHA sum file name does not match the provided JDK file name.  Validation failed!  Process will end."
		exit
	fi
	echo "Provided value matched!"

	# Before continuing, extract the JDK version...
	if [ $isOpenJDK = true ]; then
		jdkVersionToInstall=$(echo ${sourceFile:8} | cut -d'_' -f 1)

		# Now, build my comparison string with the processor type for check & balances...
		#printf -v expectedFile "openjdk-%s_linux-x%s_bin.tar.gz" $jdkVersionToInstall $processorType 
	else
		jdkVersionToInstall=$(echo ${sourceFile:4} | cut -d'_' -f 1)
	
		# Now, build my comparison string with the processor type for check & balances...
		#printf -v expectedFile "jdk-%s_linux-x%s_bin.tar.gz" $jdkVersionToInstall $processorType 
	fi

	# Future validation...
	# Confirm JDK file is for the working Linux version, i.e. 32 or 64...
	#if [ $sourceFile != $expectedFile ]; then
	#	echo "Source file [$sourceFile] is not an JDK for this Linux version!"
	#	exit
	#fi

	# If we're here is because all validations passed!
	echo "Source file [$sourceFile] is a valid JDK file!"
	
	echo "Input parameter validation passed!"
	echo ""

	# Before exiting, assigned the expected extracted directory...
	jdkExtractedDir="jdk-$jdkVersionToInstall"
}


# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
# Detect if Java is already installed.  Returns 1 if it is, otherwise 0.
# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
isJDKInstalled() 
{
	echo "*-*-*-*-*     Checking system to see if JDK is installed     *-*-*-*-*"
	echo 

	echo "Will confirm by checking if Java compiler (javac) is installed..."

	# Get where system is looking for Java...
#	jdkInstalledPath=$(`sudo --user=#$UID which javac`)
	jdkInstalledPath=$(su -l -c "javac -version" $SUDO_USER)
	if [ -z "$jdkInstalledPath" ]; then
		# Got nothing, so Java is not set up in the system!
		currentJDKStatus=$NOT_INSTALLED
	else
		# JDK is installed!  Check if it's configured through alternatives...
		echo "A JDK is installed!"
		echo
	    echo "Checking if Java is configured using alternatives..."

		# This time will check Java instead...
		jdkInstalledPath=$(sudo update-alternatives --display java | grep -i "link currently points to" | cut --characters=28-)
		if [ -z $jdkInstalledPath ]; then
			# We got nothing, so it's not configured through alternatives!
			echo "It is not!"
			currentJDKStatus=$INSTALLED_NOT_CONFIGURED
		else
			echo "It is!"

			# There is an alternative! Check if it's pointing to a script installed path...
			if [ ${jdkInstalledPath:0:17} = "$systemJavaDir/jdk-" ]; then
				# It is!
				currentJDKStatus=$INSTALLED_BY_SCRIPT
				jdkInstalledVersion=$(echo ${jdkInstalledPath:17} | cut -d'/' -f 1)		
			else
				# It is not!  Is it configured but not pointing to the script installed JDK?
				jdkInstalledPath=$(sudo update-alternatives --list java | grep -i "$systemJavaDir/jdk-" | cut -d'/' -f 5)
				if [ -z "$jdkInstalledPath" ]; then
					# Negative!  We never installed it...
					currentJDKStatus=$INSTALLED_NOT_CONFIGURED
				else
					# So we did installed a version once, but but it's pointing to another JDK!
					jdkInstalledVersion=${jdkInstalledPath:4}
					currentJDKStatus=$INSTALLED_POINTS_TO_ANOTHER_JDK
				fi
			fi
		fi
	fi

	# Lastly, inform the user what we found...
	echo ""
	case $currentJDKStatus in
		$NOT_INSTALLED) 
			echo "JDK is not installed!"
			;;

		$INSTALLED_BY_SCRIPT)
			echo "Current JDK was installed by this script! Installed version is $jdkInstalledVersion."
			;;

		$INSTALLED_NOT_CONFIGURED)
			# We are terminating!  Clean up first...
			rm -r -f $jdkExtractedDir

			# Now tell the user the script is terminating and why!
			echo "A JDK is installed, but it's configured through the system path.  Since this was not done through system's alternatives, the script cannot properly remove the current settings!"
			echo
			echo "Please manually remove the installed JDK and the re-run the script to install the new JDK."
			echo 
			echo "The script will terminate."
			;;

		$INSTALLED_POINTS_TO_ANOTHER_JDK)
			echo "The script previously installed version $jdkInstalledVersion, but Java is pointing to another JDK/JRE!"

	esac
	echo ""

	if [[ $currentJDKStatus = $NOT_INSTALLED || $currentJDKStatus = $INSTALLED_NOT_CONFIGURED ]]; then
		return 0
	fi

	return 1
}


# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
# Extract the provided tar file and validate the extracted folder is a JDK folder
# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
extractAndValidateJDK() 
{
	echo "*-*-*-*-*                Extracting JDK File                 *-*-*-*-*"
	echo

	# Before extracting, make sure there is no JDK directory in the working folder...
	# For that, declare an array and read files that start with jdk-*
	echo "Checking for previous JDK folders in working directory..."
	declare -a jdkFiles

	jdkFiles=( ./jdk-* )
	deletedFolders=false

	# Now traverse the array looking for directories...
	for (( x=0;x<${#jdkFiles[@]};x++ )); do
		if [ -d ${jdkFiles[$x]} ]; then
			deletedFolders=true
			echo ""
			echo "There is a previous JDK directory in working path - deleting it!"
			rm -r -f ${jdkFiles[${x}]}
			echo "JDK directory [${jdkFiles[${x}]}] deleted!"
			echo ""
		fi

	done

	if [ $deletedFolders = false ]; then
		echo "No folders found!"
		echo ""
	fi

	echo "Extracting JDK files..."
	tar -xf $sourceFile
	echo "Validating uncompressed tar file..."
	if [ ! -d $jdkExtractedDir ]; then
		echo "No JDK $jdkVersionToInstall directory was extrated from the file!  Please validate the provided tar file is for a JDK.  Process will end."
		exit
	else
		echo "Confirmed!  Extrated a valid JDK!"
		echo
	fi
	echo "JDK was extracted!"
	echo ""

}


# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
# Sync the extrated JDK folder to final destination
# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
moveJDKToSysFolder() 
{
	echo "*-*-*-*-*            Moving JDK to system folder             *-*-*-*-*"
	echo  
	if [ ! -d "$systemJavaDir/jdk-$jdkVersionToInstall" ]; then
		echo "Creating JDK folder for new JDK..."
		sudo mkdir -p "$systemJavaDir/jdk-$jdkVersionToInstall"
		echo "Folder created!"

	fi

	echo "Moving extracted JDK to [$systemJavaDir/jdk-$jdkVersionToInstall]..."
	sudo rsync -rl $jdkExtractedDir"/" "$systemJavaDir/jdk-$jdkVersionToInstall"
	echo "JDK moved to system folder!"
	echo ""
	rm -r -f $jdkExtractedDir
	echo "Deleting extracted files..."
	echo ""

}


# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
# Remove existing configuration if JDK is already installed
# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
removeCurrentConfiguration() 
{
	# There are two conditions when we need to remove the configured alternatives - 
	# INSTALLED_BY_SCRIPT and INSTALLED_POINTS_TO_ANOTHER_JDK!

	if [[ $currentJDKStatus = $INSTALLED_BY_SCRIPT  || $currentJDKStatus = $INSTALLED_POINTS_TO_ANOTHER_JDK ]]; then
		echo "*-*-*-*-*         Removing previous JDK alternatives         *-*-*-*-*"
		echo ""

		# Be a good citizen and only remove the alternatives that we have created!

		# Removing java...
		echo "java..."
		sudo update-alternatives --quiet --remove "java" "$systemJavaDir/jdk-$jdkInstalledVersion/bin/java" 
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi
		echo 

		# Removing javac...
		echo "javac..."
		sudo update-alternatives --quiet --remove "javac" "$systemJavaDir/jdk-$jdkInstalledVersion/bin/javac"
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi
		echo 

		# Removing jar...
		echo "jar..."
		sudo update-alternatives --quiet --remove "jar" "$systemJavaDir/jdk-$jdkInstalledVersion/bin/jar"
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi
		echo 

		#Configuring javadoc...
		echo "javadoc..."
		sudo update-alternatives --quiet --remove "javadoc" "$systemJavaDir/jdk-$jdkInstalledVersion/bin/javadoc"
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi
		echo 

		# Removing jshell...
		echo "jshell..."
		sudo update-alternatives --quiet --remove "jshell" "$systemJavaDir/jdk-$jdkInstalledVersion/bin/jshell"
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi
		echo 

		# Removing jlink...
		echo "jlink..."
		sudo update-alternatives --quiet --remove "jlink" "$systemJavaDir/jdk-$jdkInstalledVersion/bin/jlink"
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi
		echo 

		# Removing jmod...
		echo "jmod..."
		sudo update-alternatives --quiet --remove "jmod" "$systemJavaDir/jdk-$jdkInstalledVersion/bin/jmod"
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi
		echo 

		# Removing javap...
		echo "javap..."
		sudo update-alternatives --quiet --remove "javap" "$systemJavaDir/jdk-$jdkInstalledVersion/bin/javap"
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi
		echo 

		# Removing jdeps...
		echo "jdeps..."
		sudo update-alternatives --quiet --remove "jdeps" "$systemJavaDir/jdk-$jdkInstalledVersion/bin/jdeps"
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi
		echo 

		# Removing jarsigner...
		echo "jarsigner..."
		sudo update-alternatives --quiet --remove "jarsigner" "$systemJavaDir/jdk-$jdkInstalledVersion/bin/jarsigner"
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi
		echo 

		# Removing jconsole...
		echo "jconsole..."
		sudo update-alternatives --quiet --remove "jconsole" "$systemJavaDir/jdk-$jdkInstalledVersion/bin/jconsole"
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi

		# Delete current JDK...
		sudo rm -rf $systemJavaDir/jdk-$jdkInstalledVersion

		echo ""
		echo "Done!  Removed previously installed JDK version $jdkInstalledVersion configuration!"
		echo ""

	fi

 }


# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
# Configure JDK program alternatives (links)
# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
configureJDKUtilities() 
{
	echo "*-*-*-*-*        Configuring alternatives for new JDK        *-*-*-*-*"
	echo
	echo "The following JDK utilities will be configured in the system's alternatives: "
	echo ""

	userConfigMsg=""

	# Configuring java...
	echo "java..."
	sudo update-alternatives --quiet --install "/usr/bin/java" "java" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/java" 1
	if [ $? = 0 ]; then
		if [[ $currentJDKStatus = $INSTALLED_BY_SCRIPT  || $currentJDKStatus = $INSTALLED_POINTS_TO_ANOTHER_JDK ]]; then
			# I'm concluding the set will not failed since we successfully added the alternative!
			sudo update-alternatives --quiet --set "java" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/java"
		fi	
		echo "Configured!"
	else
		echo "Failed to configured \"java\"!"
	fi
	echo 

	# Configuring javac...
	echo "javac..."
	sudo update-alternatives --quiet --install "/usr/bin/javac" "javac" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/javac" 1
	if [ $? = 0 ]; then
		if [[ $currentJDKStatus = $INSTALLED_BY_SCRIPT  || $currentJDKStatus = $INSTALLED_POINTS_TO_ANOTHER_JDK ]]; then
			sudo update-alternatives --quiet --set "javac" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/javac"
		fi	
		echo "Configured!"
	else
		echo "Failed to configured \"javac\"!"
	fi
	echo 

	# Configuring jar...
	echo "jar..."
	sudo update-alternatives --quiet --install "/usr/bin/jar" "jar" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/jar" 1
	if [ $? = 0 ]; then
		if [[ $currentJDKStatus = $INSTALLED_BY_SCRIPT  || $currentJDKStatus = $INSTALLED_POINTS_TO_ANOTHER_JDK ]]; then
			sudo update-alternatives --quiet --set "jar" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/jar"
		fi	
		echo "Configured!"
	else
		echo "Failed to configured \"jar\"!"
	fi
	echo 

	# Configuring javadoc...
	echo "javadoc..."
	sudo update-alternatives --quiet --install "/usr/bin/javadoc" "javadoc" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/javadoc" 1
	if [ $? = 0 ]; then
		if [[ $currentJDKStatus = $INSTALLED_BY_SCRIPT  || $currentJDKStatus = $INSTALLED_POINTS_TO_ANOTHER_JDK ]]; then
			sudo update-alternatives --quiet --set "javadoc" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/javadoc"
		fi	
		echo "Configured!"
	else
		echo "Failed to configured \"javadoc\"!"
	fi
	echo 

	# Configuring jshell...
	echo "jshell..."
	sudo update-alternatives --quiet --install "/usr/bin/jshell" "jshell" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/jshell" 1
	if [ $? = 0 ]; then
		if [[ $currentJDKStatus = $INSTALLED_BY_SCRIPT  || $currentJDKStatus = $INSTALLED_POINTS_TO_ANOTHER_JDK ]]; then
			sudo update-alternatives --quiet --set "jshell" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/jshell"
		fi	
		echo "Configured!"
	else
		echo "Failed to configured \"jshell\"!"
	fi
	echo 

	# Configuring jlink...
	echo "jlink..."
	sudo update-alternatives --quiet --install "/usr/bin/jlink" "jlink" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/jlink" 1
	if [ $? = 0 ]; then
		if [[ $currentJDKStatus = $INSTALLED_BY_SCRIPT  || $currentJDKStatus = $INSTALLED_POINTS_TO_ANOTHER_JDK ]]; then
			sudo update-alternatives --quiet --set "jlink" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/jlink"
		fi	
		echo "Configured!"
	else
		echo "Failed to configured \"jlink\"!"
	fi
	echo 

	# Configuring jmod...
	echo "jmod..."
	sudo update-alternatives --quiet --install "/usr/bin/jmod" "jmod" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/jmod" 1
	if [ $? = 0 ]; then
		if [[ $currentJDKStatus = $INSTALLED_BY_SCRIPT  || $currentJDKStatus = $INSTALLED_POINTS_TO_ANOTHER_JDK ]]; then
			sudo update-alternatives --quiet --set "jmod" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/jmod"
		fi	
		echo "Configured!"
	else
		echo "Failed to configured \"jmod\"!"
	fi
	echo 

	# Configuring javap...
	echo "javap..."
	sudo update-alternatives --quiet --install "/usr/bin/javap" "javap" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/javap" 1
	if [ $? = 0 ]; then
		if [[ $currentJDKStatus = $INSTALLED_BY_SCRIPT  || $currentJDKStatus = $INSTALLED_POINTS_TO_ANOTHER_JDK ]]; then
			sudo update-alternatives --quiet --set "javap" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/javap"
		fi	
		echo "Configured!"
	else
		echo "Failed to configured \"javap\"!"
	fi
	echo 

	# Configuring jdeps...
	echo "jdeps..."
	sudo update-alternatives --quiet --install "/usr/bin/jdeps" "jdeps" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/jdeps" 1
	if [ $? = 0 ]; then
		if [[ $currentJDKStatus = $INSTALLED_BY_SCRIPT  || $currentJDKStatus = $INSTALLED_POINTS_TO_ANOTHER_JDK ]]; then
			sudo update-alternatives --quiet --set "jdeps" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/jdeps"
		fi	
		echo "Configured!"
	else
		echo "Failed to configured \"jdeps\"!"
	fi
	echo 

	# Configuring jarsigner...
	echo "jarsigner..."
	sudo update-alternatives --quiet --install "/usr/bin/jarsigner" "jarsigner" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/jarsigner" 1
	if [ $? = 0 ]; then
		if [[ $currentJDKStatus = $INSTALLED_BY_SCRIPT  || $currentJDKStatus = $INSTALLED_POINTS_TO_ANOTHER_JDK ]]; then
			sudo update-alternatives --quiet --set "jarsigner" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/jarsigner"
		fi	
		echo "Configured!"
	else
		echo "Failed to configured \"jarsigner\"!"
	fi
	echo 

	# Configuring jconsole...
	echo "jconsole..."
	sudo update-alternatives --quiet --install "/usr/bin/jconsole" "jconsole" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/jconsole" 1
	if [ $? = 0 ]; then
		if [[ $currentJDKStatus = $INSTALLED_BY_SCRIPT  || $currentJDKStatus = $INSTALLED_POINTS_TO_ANOTHER_JDK ]]; then
			sudo update-alternatives --quiet --set "jconsole" "$systemJavaDir/jdk-$jdkVersionToInstall/bin/jconsole"
		fi	
		echo "Configured!"
	else
		echo "Failed to configured \"jconsole\"!"
	fi

	echo ""	
	echo "Primary JDK utilities have been configured!"
	echo ""

}


# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
# 									Main
# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  

validateParams;
extractAndValidateJDK;
isJDKInstalled;

# Do we need to remove any system configurations from a previosly installed JDK?
if [ $? = 1 ]; then
	# Yes!  Removing existing settings even if it's the same Java version; original install may have failed!
	removeCurrentConfiguration;
fi	

# Exit the installation if there is a JDK installed outside of the system configurations - i.e. $PATH
if [ $currentJDKStatus = $INSTALLED_NOT_CONFIGURED ]; then
	exit
fi

moveJDKToSysFolder;
configureJDKUtilities;

echo "Running java version to verify installation..."
echo 
echo `java -version`



