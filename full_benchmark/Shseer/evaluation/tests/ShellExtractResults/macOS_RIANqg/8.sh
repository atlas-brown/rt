#!/bin/bash

# cURL Install Trusted Vendor Download

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Jamf policy parameters
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

proxy="$4"
# optional, HTTP proxy address
# e.g. http://proxy.company.com:port

downloadDirectory="$5"
# e.g. /Library/myOrg/Packages

sourceUrl="$6"
# Can be a specific file URL or a dynamic web link.
# e.g. 	https://dl.google.com/chrome/mac/stable/GGRO/googlechrome.dmg
#		https://www.vendor.com/latestDownload
# For security's sake, ONLY USE HTTPS LINKS FROM KNOWN GOOD VENDOR SOURCES

checksumAvailable="$7"
# Optional - Make non-null to trigger checksum validation for download.

	checksumSource="$8"
	# Source file for checksum data
	
	checksumParse="$9"
	# Command(s) to parse checksum from $checksumSource

applicationPath="$10"
# e.g. /Applications/Microsoft Word.app
# Do not include escape characters

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# SYSTEM VARIABLES
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

timeStamp=$(date +"%F %T")

# Set proxy argument if necessary
# checks if this external resource is available.
# below is an example. recommend using something externally available-only that your org owns.
officeReleaseXml=$(curl https://macadmins.software/latest.xml)
if [ "$officeReleaseXml" = "" ]; then
	proxyArgument="-x $proxy"
fi

# Get final download URL
finalownloadUrl=$(curl $proxyArgument "$sourceUrl" -s -L -I -o /dev/null -w '%{url_effective}')

# Get download file name
downloadFile=$(basename "$finalownloadUrl")

# Get download file extension
downloadExt=$({downloadFile##*.})
downloadExt=$(echo "$downloadExt" | tr '[:upper:]' '[:lower:]')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# FUNCTIONS
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

downloadFile(){
	# rm contents of $downloadDirectory
	# DOWNLOAD
}

validateChecksum(){
	# Read $checksumSource to $checksumData
	# Parse $checksumData to $checksumCorrect using $checksumParse
	# Get downloaded file's checksum in $checksumDownloadedFile
	# Compare $checksumCorrect to $checksumDownloadedFile
		# if equal, return
		# else delete downloaded file, exit with error 1
}

validatePkgSignature(){
	# if bad, error 2
}

validateAppSignature(){
	# if bad, error 3
}

installApplication(){

# DETERMINE PKG, DMG, or APP

# CASE install for each
	# PKG and APP - check signature and error, exit, and delete offending file(s) on fail.
case $downloadExt in
    pkg)
		# install package
		;;
    app)
		# move to /Applications
		;;
	dmg)
		# Mount dmg
		# Find app bundle(s) and/or pkgs at root of DMG, populate array $itemsToInstall
		# Loop through $itemsToInstall
			# if pkg; install pkg
				# elif app; copy app to /Applications
		;;
	esac

}

cleanUp(){
	for filename in $downloadDirectory/*; do
		rm -rf $filename
	done
}

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Main Application
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

downloadFile

if [ -n "$checksumAvailable" ]; then
	validateChecksum
fi

case $downloadExt in
	pkg)
		validatePkgSignature
		;;
	app)
		validateAppSignature
		;;
	dmg)
		:
		;;
	*)
		printf "$timeStamp %s\n" "Downloaded $downloadFile from..."
		printf "$timeStamp %s\n" "$finalownloadUrl"
		printf "$timeStamp %s\n" "is an unknown file type."
		rm -rf "$downloadDirectory"/"$downloadFile"
		printf "$timeStamp %s\n" "Deleted $downloadFile."
		exit 4
		
	esac 

installApplication

validateAppSignature

cleanUp

exit 0
