#!/bin/bash

# Install Zoom Client and Zoom Plugin for Microsoft Outlook

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Jamf policy parameters
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

proxy="$4"
# optional, HTTP proxy address
# e.g. http://proxy.company.com:port

downloadDirectory="$5"
# e.g. /Library/myOrg/Packages

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# SYSTEM VARIABLES
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

timeStamp=$(date +"%F %T")

failedInstallCount=0

zoomClientUrl="https://zoom.us/client/latest/Zoom.pkg"

zoomPluginUrl="https://zoom.us/client/latest/ZoomMacOutlookPlugin.pkg"

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
	
		# Get package name
		pkgName=$(printf "%s" "${zoomDownload[@]}" | sed 's@.*/@@')
		
		# Set application path
		if [ "$pkgName" = "Zoom.pkg" ]; then
			applicationPath=("/Applications/zoom.us.app")
		else
			applicationPath=("/Applications/ZoomOutlookPlugin/PluginLauncher.app" "/Applications/ZoomOutlookPlugin/Uninstall.app")
			
		
		# Set proxy argument if necessary
		officeReleaseXml=$(curl https://macadmins.software/latest.xml)
		if [ "$officeReleaseXml" = "" ]; then
			proxyArgument="-x $proxy"
		fi
	
		# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
		# Function
		# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	
		# Download package
		printf "$timeStamp %s\n" "Downloading $pkgName."
		curl --retry 3 --create-dirs $proxyArgument -o "$downloadDirectory"/"$pkgName" -O "$zoomDownload"
		curlExitCode=$?
				# Download error handling
				if [ "$curlExitCode" -ne 0 ]; then
					printf "$timeStamp %s\n" "Failed to download: %s\n" "$pkgName"
					printf "$timeStamp %s\n" "Curl exit code: %s\n" "$curlExitCode"
					((failedInstallCount++))
					return
				else
					printf "$timeStamp %s\n" "Successfully downloaded $pkgName."
				fi
		
		# Check package signature
		printf "$timeStamp %s\n" "Checking signature on $pkgName."
		signatureStatus=$(/usr/sbin/pkgutil --check-signature "$downloadDirectory"/"$pkgName" | grep "Status:")
		# if status has Apple Root CA, continue. Otherwise delete pkg, notify, exit
		if [[ $signatureStatus != *"signed by a certificate trusted"* ]]; then
			printf "$timeStamp %s\n" "Bad package signature. Aborting installation."
			printf "$timeStamp %s\n" "Deleting package with bad signature."
			printf "$timeStamp %s\n" "Failed to install $pkgName."
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
			printf "$timeStamp %s\n" "Failed to install $pkgName."
			((failedInstallCount++))
			return
		fi
		
		# Check app signature
		for path in "${applicationPath[@]}"; do
			appSignature=$(/usr/sbin/pkgutil --check-signature "$path" | grep "Status:")
			echo "Application Signature $appSignature"
			# if Apple Root CA and good hash, continue, else delete app, delete package, notify, and exit.
			if [[ $signatureStatus != *"signed by a certificate trusted"* ]]; then
					printf "$timeStamp %s\n" "Bad application signature. Deleting application"
					printf "$timeStamp %s\n" "Failed to install $pkgName."
					rm -rf "$downloadDirectory"/"$pkgName"
					rm -rf "$applicationPath"
					((failedInstallCount++))
					return
				else
					echo "Package Signature $signatureStatus"
			fi	
		done
	}

	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
	# Function: cleanUp
	# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

	cleanUp(){
	for filename in $downloadDirectory/Zoom*.pkg; do
		rm -rf $filename
	done
	}

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
# Main Application
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

for zoomDownload in $zoomClientUrl $zoomPluginUrl; do
	cleanUp
	downloadInstallAndValidate
	cleanUp
	done
	
exit $failedInstallCount
