#!/bin/bash

# Install all the desired Office Apps with one script

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Jamf policy parameters
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

apps="$4"
# one or more of the following application identifiers (case sensitive), space separated
# Word Excel PowerPoint Outlook OneNote OneDrive Skype Teams Intune Remote MAU
#
# Note: OneNote, OneDrive, and Remote Desktop are available via the Mac App Store. It is recommended to deploy those apps via VPP.

license="$5"
# 365 or 2016

proxy="$6"
# optional, HTTP proxy address
# e.g. http://proxy.company.com:port

downloadDirectory="$7"
# e.g. /Library/myOrg/Packages

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# SYSTEM VARIABLES
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

timeStamp=$(date +"%F %T")

appsToInstall="$4"

failedInstallCount=0

# get MS Office release XML
officeReleaseXml=$(curl https://macadmins.software/latest.xml)
# Correct if proxy is necessary
	if [ "$officeReleaseXml" = "" ]; then
		proxyArgument="-x $proxy"
		officeReleaseXml=$(curl $proxyArgument https://macadmins.software/latest.xml)
	fi

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# FUNCTIONS
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	# Function: downloadInstallAndValidate
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

	downloadInstallAndValidate(){
	
		# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
		# Function Variables
		# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	
		# Create title string
		if [[ $app != *"MAU"* ]]; then
			appTitle="$app $license"
			applicationPath="/Applications/Microsoft $app.app"
		else
			appTitle="$app"
			applicationPath="/Library/Application Support/Microsoft/MAU2.0/Microsoft AutoUpdate.app"
		fi	
	
		# Create title xpath search string
		appTitleSearch=$"'"$appTitle"'"
	
		# Get download URL
		downloadUrl=$(echo $officeReleaseXml | /usr/bin/xpath "/latest/package[title[contains(text(), $appTitleSearch)]]/download/text()")
	
		# Get final download URL
		finalDownloadUrl=$(curl $proxyArgument "$downloadUrl" -s -L -I -o /dev/null -w '%{url_effective}')
	
		# Get package name
		pkgName=$(printf "%s" "${finalDownloadUrl[@]}" | sed 's@.*/@@')
	
		# Get download sha256 hash
		correctHash=$(echo $officeReleaseXml | /usr/bin/xpath "/latest/package[title[contains(text(), $appTitleSearch)]]/sha256/text()")
	
		# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
		# Function
		# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	
		# Download package
		printf "$timeStamp %s\n" "Downloading $pkgName."
		curl --retry 3 --create-dirs $proxyArgument -o "$downloadDirectory"/"$pkgName" -O "$finalDownloadUrl"
		curlExitCode=$?
				# Download error handling
				if [ "$curlExitCode" -ne 0 ]; then
					printf "$timeStamp %s\n" "Failed to download: %s\n" "$finalDownloadUrl"
					printf "$timeStamp %s\n" "Curl exit code: %s\n" "$curlExitCode"
					((failedInstallCount++))
					return
				else
					printf "$timeStamp %s\n" "Successfully downloaded $pkgName."
				fi
	
		
		# Check package hash
		printf "$timeStamp %s\n" "Checking SHA256 hash for $pkgName."
		printf "$timeStamp %s\n" "The package hash should be $correctHash"
		downloadHash=$(/usr/bin/shasum -a 256 "$downloadDirectory"/"$pkgName" | awk '{print $1}')
		printf "$timeStamp %s\n" "The downloaded package hash is $downloadHash"
		# If hashes match, continue. Otherwise delete pkg, notify, exit
		if [ "$correctHash" != "$downloadHash" ];then
			printf "$timeStamp %s\n" "Bad hash. Aborting installation."
			printf "$timeStamp %s\n" "Deleting package with bad hash."
			printf "$timeStamp %s\n" "Failed to install $appTitle."
			((failedInstallCount++))
			rm -rf "$downloadDirectory"/"$pkgName"
			return
		fi	
		
		# Check package signature
		printf "$timeStamp %s\n" "Checking signature on $pkgName."
		signatureStatus=$(/usr/sbin/pkgutil --check-signature "$downloadDirectory"/"$pkgName" | grep "Status:")
		# if status has Apple Root CA, continue. Otherwise delete pkg, notify, exit
		if [[ $signatureStatus != *"signed by a certificate trusted"* ]]; then
			printf "$timeStamp %s\n" "Bad package signature. Aborting installation."
			printf "$timeStamp %s\n" "Deleting package with bad signature."
			printf "$timeStamp %s\n" "Failed to install $appTitle."
			((failedInstallCount++))
			rm -rf "$downloadDirectory"/"$pkgName"
			return
		else
			printf "$timeStamp %s\n" "Package Signature $signatureStatus"
		fi	
		
		# Install
		installer -pkg "$downloadDirectory"/"$pkgName" -target /
		if [ $? -eq 0 ]
		then
			printf "$timeStamp %s\n" "Installed $pkgName successfully."
		else
			printf "$timeStamp %s\n" "Installation of $pkgName failed."
			printf "$timeStamp %s\n" "Failed to install $appTitle."
			((failedInstallCount++))
			return
		fi
		
		# Check app signature
		appSignature=$(/usr/sbin/pkgutil --check-signature "$applicationPath" | grep "Status:")
		echo "Application Signature $appSignature"
		# if Apple Root CA and good hash, continue, else delete app, delete package, notify, and exit.
		if [[ $signatureStatus != *"signed by a certificate trusted"* ]]; then
				printf "$timeStamp %s\n" "Bad application signature. Deleting application"
				printf "$timeStamp %s\n" "Failed to install $appTitle."
				rm -rf "$downloadDirectory"/"$pkgName"
				rm -rf "$applicationPath"
				((failedInstallCount++))
				return
			else
				echo "Package Signature $signatureStatus"
		fi	
		
	}

	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	# Function: cleanUp
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

	cleanUp(){
	for filename in $downloadDirectory/Microsoft*.pkg; do
		rm -rf $filename
	done
	}

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Main Application
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

for app in $apps; do
	cleanUp
	downloadInstallAndValidate
	cleanUp
	done
	
exit $failedInstallCount
