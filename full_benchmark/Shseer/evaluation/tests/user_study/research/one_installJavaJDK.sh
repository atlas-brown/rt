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


# Global variables...
isOpenJDK=true
javaIsInstalled=false
installedJDK=""
installedVersion=""
systemJavaDir="/usr/lib/jvm"
jdkVersion=""
processorType=$(getconf LONG_BIT)
jdkExtractedDir=""

scriptVersion="1.0"

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
		echo "Installs the provided the JDK.  It confirms the tar SHA256 sum matches that of the provided value and performs simple validation to verify the provided tar contains a JDK folder.  Script can intall either an Oracle or OpenJDK 9 or greater JDK.  Installation script has been tested on Ubuntu.  Go to project home page (https://github.com/jhenriquez418/linux-java-jdk-installer) for further info."
		echo ""
		echo "Script must be executed with sudo.  For example:"
		echo ""
		echo "sudo ./installJavaJDK jdk-10_linux-x64_bin.tar.gz 0b14aaecd5323457bd15dc7798d08181ad04bad4156e55387ed714190912a9ce"
		echo ""
		echo "installJavaJDK version $scriptVersion"
		echo "Copyright (c) 2018 Jose Henriquez [https://github.com/jhenriquez418/linux-java-jdk-installer]"
		echo "MIT License"
		echo ""
		echo 'THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.'
		echo ""
		exit
	fi
		
	echo "*-*-*-*-*     Validating script parameters     *-*-*-*-*"
	echo ""

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
		jdkVersion=$(echo ${sourceFile:8} | cut -d'_' -f 1)

		# Now, build my comparison string with the processor type for check & balances...
		#printf -v expectedFile "openjdk-%s_linux-x%s_bin.tar.gz" $jdkVersion $processorType 
	else
		jdkVersion=$(echo ${sourceFile:4} | cut -d'_' -f 1)
	
		# Now, build my comparison string with the processor type for check & balances...
		#printf -v expectedFile "jdk-%s_linux-x%s_bin.tar.gz" $jdkVersion $processorType 
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
	jdkExtractedDir="jdk-$jdkVersion"
}


# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
# Detect if Java is already installed
# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
isJavaInstalled() 
{
	echo "*-*-*-*-*     Checking system to see if JDK is installed     *-*-*-*-*"
	echo 

	declare -a installedJDK

	installedJDK=( $systemJavaDir/* )

	# Simple check, did we read any files?
	if [ ${installedJDK[0]} = "$systemJavaDir/*" ]; then
		echo "It is not!"
		echo
		return 0
	fi

	# So we got files!  Go through each of them to confirm it's a JDK folder...
	for (( x=0;x<${#installedJDK[@]};x++ )); do
		if [[ ${installedJDK[$x]} != "/usr/lib/jvm/jdk-$jdkVersion" && -d ${installedJDK[$x]} ]]; then
			installedJDK=${installedJDK[$x]}
			installedVersion=${installedJDK[$x]:17}
			javaIsInstalled=true

			echo "Yes!  Found JDK $installedVersion installed!"
			echo 
			return 1
		else
			if [[ ${installedJDK[$x]} = "/usr/lib/jvm/jdk-$jdkVersion" && -d ${installedJDK[$x]} ]]; then
				javaIsInstalled=true
				echo "JKD $jdkVersion is already installed!  Overriding settings..."
				echo
				return 1
			fi
		fi

	done

}


# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
# Extract the provided tar file and validate the extracted folder is a JDK folder
# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
extractAndValidateJDK() 
{
	echo "*-*-*-*-*     Extracting JDK File     *-*-*-*-*"
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
		echo "No JDK $jdkVersion directory was extrated from the file!  Process will end."
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
	echo "*-*-*-*-*     Moving JDK to system folder    *-*-*-*-*"
	echo  
	if [ ! -d "$systemJavaDir/jdk-$jdkVersion" ]; then
		echo "Creating JVM folder since Java is not installed..."
		sudo mkdir -p "$systemJavaDir/jdk-$jdkVersion"
		echo "Folder created!"

	fi

	echo "Moving extracted JDK to [$systemJavaDir/jdk-$jdkVersion]..."
	sudo rsync -rl $jdkExtractedDir"/" "$systemJavaDir/jdk-$jdkVersion"
	echo "JDK moved to system folder!"
	echo ""
	rm -r -f $jdkExtractedDir
	echo "Deleting extracted files..."
	echo ""

}


# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
# Remove existing configuration if java JDK is already installed
# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
removeCurrentConfiguration() 
{
	if [ $javaIsInstalled = true ]; then
		echo "*-*-*-*-*     Removing previous Java version links    *-*-*-*-*"
		echo ""

		# Removing java...
		echo "java..."
		sudo update-alternatives --quiet --remove-all "java"
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi
		echo 

		# Removing javac...
		echo "javac..."
		sudo update-alternatives --quiet --remove-all "javac"
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi
		echo 

		# Removing jar...
		echo "jar..."
		sudo update-alternatives --quiet --remove-all "jar"
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi
		echo 

		# Removing  javaws, if it exist in the current JDK bin folder!
		if [ -f "$systemJavaDir/jkd-$installedJDK/bin/javaws" ]; then
			echo "javaws..."
			sudo update-alternatives --remove-all "javaws"
			if [ $? = 0 ]; then
				echo "Removed!"
			else
				echo "Huummm... there was an error!  We'll continue anyway..."
			fi
			echo 
		fi

		#Configuring javadoc...
		echo "javadoc..."
		sudo update-alternatives --quiet --remove-all "javadoc"
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi
		echo 

		# Removing jshell...
		echo "jshell..."
		sudo update-alternatives --quiet --remove-all "jshell"
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi
		echo 

		# Removing jlink...
		echo "jlink..."
		sudo update-alternatives --quiet --remove-all "jlink"
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi
		echo 

		# Removing jmod...
		echo "jmod..."
		sudo update-alternatives --quiet --remove-all "jmod"
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi
		echo 

		# Removing javap...
		echo "javap..."
		sudo update-alternatives --quiet --remove-all "javap"
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi
		echo 

		# Removing jdeps...
		echo "jdeps..."
		sudo update-alternatives --quiet --remove-all "jdeps"
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi
		echo 

		# Removing jarsigner...
		echo "jarsigner..."
		sudo update-alternatives --quiet --remove-all "jarsigner"
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi
		echo 

		# Removing jconsole...
		echo "jconsole..."
		sudo update-alternatives --quiet --remove-all "jconsole"
		if [ $? = 0 ]; then
			echo "Removed!"
		else
			echo "Huummm... there was an error!  We'll continue anyway..."
		fi

		# Delete current JDK...
		sudo rm -rf $systemJavaDir/jdk-$installedVersion

		echo ""
		echo "Done!  Existing configuration have been removed!"
		echo ""

		# Update our installed flag to false...
		javaIsInstalled=false
	fi

 }


# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
# Configure JDK program links (using alternatives)
# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
configureJava() 
{
	if [ $javaIsInstalled = false ]; then
		echo "*-*-*-*-*     Configuring Java     *-*-*-*-*"
		echo
		echo "The following will be added to your alternatives: "
		echo ""

		# Configuring java...
		echo "java..."
		sudo update-alternatives --quiet --install "/usr/bin/java" "java" "$systemJavaDir/jdk-$jdkVersion/bin/java" 1
		if [ $? = 0 ]; then
			echo "Configured!"
		else
			echo "Failed to configured \"java\"!"
		fi
		echo 

		# Configuring javac...
		echo "javac..."
		sudo update-alternatives --quiet --install "/usr/bin/javac" "javac" "$systemJavaDir/jdk-$jdkVersion/bin/javac" 1
		if [ $? = 0 ]; then
			echo "Configured!"
		else
			echo "Failed to configured \"javac\"!"
		fi
		echo 

		# Configuring jar...
		echo "jar..."
		sudo update-alternatives --quiet --install "/usr/bin/jar" "jar" "$systemJavaDir/jdk-$jdkVersion/bin/jar" 1
		if [ $? = 0 ]; then
			echo "Configured!"
		else
			echo "Failed to configured \"jar\"!"
		fi
		echo 

		# Configuring javaws... available only in Oracle JDK!!!
		if [ $isOpenJDK = false ]; then
			echo "javaws..."
			sudo update-alternatives --quiet --install "/usr/bin/javaws" "javaws" "$systemJavaDir/jdk-$jdkVersion/bin/javaws" 1
			if [ $? = 0 ]; then
				echo "Configured!"
			else
				echo "Failed to configured \"javaws\"!"
			fi
			echo 
		fi

		# Configuring javadoc...
		echo "javadoc..."
		sudo update-alternatives --quiet --install "/usr/bin/javadoc" "javadoc" "$systemJavaDir/jdk-$jdkVersion/bin/javadoc" 1
		if [ $? = 0 ]; then
			echo "Configured!"
		else
			echo "Failed to configured \"javadoc\"!"
		fi
		echo 

		# Configuring jshell...
		echo "jshell..."
		sudo update-alternatives --quiet --install "/usr/bin/jshell" "jshell" "$systemJavaDir/jdk-$jdkVersion/bin/jshell" 1
		if [ $? = 0 ]; then
			echo "Configured!"
		else
			echo "Failed to configured \"jshell\"!"
		fi
		echo 

		# Configuring jlink...
		echo "jlink..."
		sudo update-alternatives --quiet --install "/usr/bin/jlink" "jlink" "$systemJavaDir/jdk-$jdkVersion/bin/jlink" 1
		if [ $? = 0 ]; then
			echo "Configured!"
		else
			echo "Failed to configured \"jlink\"!"
		fi
		echo 

		# Configuring jmod...
		echo "jmod..."
		sudo update-alternatives --quiet --install "/usr/bin/jmod" "jmod" "$systemJavaDir/jdk-$jdkVersion/bin/jmod" 1
		if [ $? = 0 ]; then
			echo "Configured!"
		else
			echo "Failed to configured \"jmod\"!"
		fi
		echo 

		# Configuring javap...
		echo "javap..."
		sudo update-alternatives --quiet --install "/usr/bin/javap" "javap" "$systemJavaDir/jdk-$jdkVersion/bin/javap" 1
		if [ $? = 0 ]; then
			echo "Configured!"
		else
			echo "Failed to configured \"javap\"!"
		fi
		echo 

		# Configuring jdeps...
		echo "jdeps..."
		sudo update-alternatives --quiet --install "/usr/bin/jdeps" "jdeps" "$systemJavaDir/jdk-$jdkVersion/bin/jdeps" 1
		if [ $? = 0 ]; then
			echo "Configured!"
		else
			echo "Failed to configured \"jdeps\"!"
		fi
		echo 

		# Configuring jarsigner...
		echo "jarsigner..."
		sudo update-alternatives --quiet --install "/usr/bin/jarsigner" "jarsigner" "$systemJavaDir/jdk-$jdkVersion/bin/jarsigner" 1
		if [ $? = 0 ]; then
			echo "Configured!"
		else
			echo "Failed to configured \"jarsigner\"!"
		fi
		echo 

		# Configuring jconsole...
		echo "jconsole..."
		sudo update-alternatives --quiet --install "/usr/bin/jconsole" "jconsole" "$systemJavaDir/jdk-$jdkVersion/bin/jconsole" 1
		if [ $? = 0 ]; then
			echo "Configured!"
		else
			echo "Failed to configured \"jconsole\"!"
		fi

		echo ""	
		echo "Primary Java executables have been configured!"
		echo ""

	fi

}


# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  
# 					Main
# *-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*-*  

validateParams;
extractAndValidateJDK;
isJavaInstalled;
if [ $? = 1 ]; then
	# It is!  Removing existing settings even if it's the same Java version; original install may have failed!
	removeCurrentConfiguration;
fi	

moveJDKToSysFolder;
configureJava;

#echo "Confirming installation is complete; executing java -version"
echo "Running java version to verify installation..."
echo 
echo `java -version`


