#!/bin/bash

#### ABOUT
#
# cURLInstallOffice2016Apps.bash
#
# Process
#	• Download and install package from Microsoft HTTPS
#	• Check package hash
#	• Check package signature
#	• Install package
#	• Check app signature
#
# Instructions
#	• Populate variables via Jamf Pro parameters
#
# Errors
# 	1:	No downloadURL provided
# 	2:	No downloadDirectory provided
# 	3:	No productName provided
#	4:	No applicationPath provided
# 	5:	Download error
#	99:	Bad data - failed checksum or code signature check
####

#### VARIABLES
downloadUrl="$4"
# e.g. https://go.microsoft.com/fwlink/?linkid=525134
# copy from macadmins.software
downloadDirectory="$5"
# e.g. /Library/myOrg/Packages
productName="$6"
# copy from "Latest Released Installer Package" column @ macadmins.software
# e.g. "Word Standalone"
# Do not include quotes
applicationPath="$7"
# e.g. /Applications/Microsoft Word.app
# Do not include escape characters
proxyUrl="$8"
# Full URL for proxy server to use for curl commands in the form of http://proxy.domain.ext:port
# If not populated, downloads will be attempted without proxy.

	if [ -z "$downloadUrl" ]; then
		printf "Parameter 4 is empty. %s\n" "Populate parameter 4 with the package download URL."
		exit 1
	fi
	
	if [ -z "$downloadDirectory" ]; then
		printf "Parameter 5 is empty. %s\n" "Populate parameter 5 with the package download directory path."
		exit 2
	fi

	if [ -z "$productName" ]; then
		printf "Parameter 6 is empty. %s\n" "Populate parameter 6 with the product name as shown at macadmins.software."
		exit 3
	fi

	if [ -z "$applicationPath" ]; then
		printf "Parameter 7 is empty. %s\n" "Populate parameter 6 with the path to the installed application."
		exit 4
	fi
	
	if [ -z "$proxyUrl" ]; then
		printf "Parameter 8 is empty. %s\n" "Downloads will be attempted without proxy."
	fi
	
####

#### DERIVED VALUES
# Build proxy option for curl commands
if [ -n "$proxyUrl" ]; then
	printf "Using $proxyUrl proxy for downloads."
	addProxyToCurl="-x $proxyUrl"
fi

# Get package URL
finalDownloadUrl=$(curl "$downloadUrl" -s -L -I -o /dev/null -w '%{url_effective}' $addProxyToCurl )

# Get package name
pkgName=$(printf "%s" "${finalDownloadUrl[@]}" | sed 's@.*/@@')

####

#### DOWNLOAD PACKAGE
echo "Downloading $pkgName"
curl --retry 3 --create-dirs -o "$downloadDirectory"/"$pkgName" -O "$finalDownloadUrl" $addProxyToCurl
curlExitCode=$?
	if [ "$curlExitCode" -ne 0 ]; then
		printf "Failed to download: %s\n" "$finalDownloadUrl"
		printf "Curl exit code: %s\n" "$curlExitCode"
		exit 5
	else
		printf "Successfully downloaded $pkgName"
	fi
####

#### CHECK PACKAGE HASH
# get hash from macadmins.software
correctHash=$(curl "https://macadmins.software" $addProxyToCurl | sed -n '/Volume License/,$p' | sed -n '/<table*/,/<\/table>/p' | sed '/<\/table>/q' | grep "$productName" | awk -F "<td>|<td*>|</td>" '{print $5}')
echo "The package hash should be $correctHash"
# get hash from downloaded package
downloadHash=$(/usr/bin/shasum -a 1 "$downloadDirectory"/"$pkgName" | awk '{print $1}')
echo "The package hash is $downloadHash"
# if status has Apple Root CA, continue. Otherwise delete pkg, notify, exit
if [ "$correctHash" != "$downloadHash" ];then
	echo "Bad hash! Abort! Abort!"
	rm -rf "$downloadDirectory"/"$pkgName"
	exit 99
fi	
####

#### CHECK PACKAGE SIGNATURE
# check signature status
signatureStatus=$(/usr/sbin/pkgutil --check-signature "$downloadDirectory"/"$pkgName" | grep "Status:")
# if status has Apple Root CA, continue. Otherwise delete pkg, notify, exit
if [[ $signatureStatus != *"signed by a certificate trusted"* ]]; then
		echo "Bad package signature! Abort! Abort!"
		rm -rf "$downloadDirectory"/"$pkgName"
		exit 99
	else
		echo "Package Signature $signatureStatus"
fi	
####

#### INSTALL PACKAGE
installer -pkg "$downloadDirectory"/"$pkgName" -target /
if [ $? -eq 0 ]
then
	echo "Installed $pkgName successfully."
else
	echo "Installation of $pkgName failed."
	exit 99
fi
####

#### CHECK APP SIGNATURE
appSignature=$(/usr/sbin/pkgutil --check-signature "$applicationPath" | grep "Status:")
echo "Application Signature $appSignature"
# if Apple Root CA and good hash, continue, else delete app, delete package, notify, and exit.
if [[ $signatureStatus != *"signed by a certificate trusted"* ]]; then
		echo "Bad application signature! Abort! Abort!"
		rm -rf "$downloadDirectory"/"$pkgName"
		rm -rf "$applicationPath"
		exit 99
	else
		echo "Package Signature $signatureStatus"
fi	
####

#### CLEAN UP
rm -rf "$downloadDirectory"/"$pkgName"
####

exit 0
