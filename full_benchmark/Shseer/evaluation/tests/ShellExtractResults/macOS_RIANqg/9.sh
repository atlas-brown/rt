#!/bin/bash

#### ABOUT
#
# cURLInstallOffice365Apps.bash
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
# 	1:		No downloadURL provided
# 	2:		No downloadDirectory provided
# 	3:		No productName provided
#	4:		No applicationPath provided
# 	5:		Download error
# 	401:	Bad download hash
# 	405:	Bad package signature
# 	408:	Package installation failure
# 	406:	Bad application signature
####

#### VARIABLES
downloadUrl="$4"
# e.g. https://go.microsoft.com/fwlink/?linkid=525134
# copy from macadmins.software
downloadDirectory="$5"
# e.g. /Library/myOrg/Packages

	# 20180820 - NOW DERIVING PRODUCT NAME FROM MS XML. See line 93
	# productName="$6"
	# copy keyphrase from "Latest Released Package" column @ macadmins.software
	# e.g. "Word 365"
	# Do not include quotes

applicationPath="$7"
# e.g. /Applications/Microsoft Word.app
# Do not include escape characters
proxy="$8"
# optional, HTTP proxy address
# e.g. http://proxy.company.com:port

	if [ -z "$downloadUrl" ]; then
		printf "Parameter 4 is empty. %s\n" "Populate parameter 4 with the package download URL."
		exit 1
	fi
	
	if [ -z "$downloadDirectory" ]; then
		printf "Parameter 5 is empty. %s\n" "Populate parameter 5 with the package download directory path."
		exit 2
	fi

	# 20180820 - NOW DERIVING PRODUCT NAME FROM MS XML. See line 93
	# if [ -z "$productName" ]; then
	# 	printf "Parameter 6 is empty. %s\n" "Populate parameter 6 with the product name as shown at macadmins.software."
	# 	exit 3
	# fi

	if [ -z "$applicationPath" ]; then
		printf "Parameter 7 is empty. %s\n" "Populate parameter 6 with the path to the installed application."
		exit 4
	fi
####

#### DERIVED VALUES

# clear proxyArgument
proxyArgument=""

# Get package URL
finalDownloadUrl=$(curl "$downloadUrl" -s -L -I -o /dev/null -w '%{url_effective}')
	# Correct if proxy is necessary
	if [ "$downloadUrl" = "$finalDownloadUrl" ]; then
		proxyArgument="-x $proxy"
		finalDownloadUrl=$(curl $proxyArgument "$downloadUrl" -s -L -I -o /dev/null -w '%{url_effective}')
	fi

# Get package name
pkgName=$(printf "%s" "${finalDownloadUrl[@]}" | sed 's@.*/@@')

# get MS Office release XML
officeReleaseXml=$(curl $proxyArgument https://macadmins.software/latest.xml)

# generate downloadURL xpath search syntax
downloadUrlXpathSearch=$"'"$downloadUrl"'"

# get product name
productName=$(echo $officeReleaseXml | /usr/bin/xpath "/latest/package[download[contains(text(), $downloadUrlXpathSearch)]]/title/text()")

# get package SHA 256 hash
correctHash=$(echo $officeReleaseXml | /usr/bin/xpath "/latest/package[download[contains(text(), $downloadUrlXpathSearch)]]/sha256/text()")

####

#### DOWNLOAD PACKAGE
echo "Downloading $pkgName"

# Download, with proxy if necessary
curl --retry 3 --create-dirs $proxyArgument -o "$downloadDirectory"/"$pkgName" -O "$finalDownloadUrl"
curlExitCode=$?

# download error handling
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
echo "The package hash should be $correctHash"
# get hash from downloaded package
downloadHash=$(/usr/bin/shasum -a 256 "$downloadDirectory"/"$pkgName" | awk '{print $1}')
echo "The package hash is $downloadHash"
# if status has Apple Root CA, continue. Otherwise delete pkg, notify, exit
if [ "$correctHash" != "$downloadHash" ];then
	echo "Bad hash! Abort! Abort!"
	rm -rf "$downloadDirectory"/"$pkgName"
	exit 401
fi	
####

#### CHECK PACKAGE SIGNATURE
# check signature status
signatureStatus=$(/usr/sbin/pkgutil --check-signature "$downloadDirectory"/"$pkgName" | grep "Status:")
# if status has Apple Root CA, continue. Otherwise delete pkg, notify, exit
if [[ $signatureStatus != *"signed by a certificate trusted"* ]]; then
		echo "Bad package signature! Abort! Abort!"
		rm -rf "$downloadDirectory"/"$pkgName"
		exit 405
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
	exit 408
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
		exit 406
	else
		echo "Package Signature $signatureStatus"
fi	
####

#### CLEAN UP
rm -rf "$downloadDirectory"/"$pkgName"
####

exit 0
