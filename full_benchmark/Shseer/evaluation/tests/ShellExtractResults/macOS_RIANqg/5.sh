#!/bin/bash

# installVendorPkgFromHttps.bash

# Download and install package from vendor's HTTPS

# Populate $4 with vendor's download URL
# ONLY populate $4 with known good HTTPS URLs
# A null $4 returns an error

# Populate $5 with a space-delimited list of the installer choices that will be toggled.
# A null $5 skips the installer choices argument

# Variables
downloadUrl="$4"
downloadDirectory="/Library/myOrg/Packages"

	if [ -z "$4" ]; then
		printf "Parameter 4 is empty. %s\n" "Populate parameter 4 with the package download URL."
		exit 3
	fi

installerChoices="$5"
	if [ -n "$5" ]; then
		choiceFile="$downloadDirectory/installerChoices.xml"
		echo '<array>' > "$choiceFile" 
			for choice in $installerChoices; do
            	echo '	<string>'"$choice"'</string>' >> "$choiceFile"
        	done
        echo '</array>' >> "$choiceFile"
        installerChoicesArgument="-applyChoiceChangesXML $choiceFile"
    else
    	printf "Parameter 5 is empty. %s\n" "No installer choices will be applied."
	fi

# Get package URL
finalDownloadUrl=$(curl "$downloadUrl" -s -L -I -o /dev/null -w '%{url_effective}')

# Get package name
pkgName=$(printf "%s" "${finalDownloadUrl[@]}" | sed 's@.*/@@')

# Download package
curl --retry 3 --create-dirs -o "$downloadDirectory"/"$pkgName" -O "$finalDownloadUrl"
curlExitCode=$?
	if [ "$curlExitCode" -ne 0 ]; then
		printf "Failed to download: %s\n" "$finalDownloadUrl"
		printf "Curl exit code: %s\n" "$curlExitCode"
		exit 1
	else
		printf "Successfully downloaded $pkgName"
	fi

# Install package
installer -pkg "$downloadDirectory"/"$pkgName" -target / "$installerChoicesArgument" -verbose
installerExitCode=$?
	if [ "$installerExitCode" -ne 0 ]; then
		printf "Failed to install: %s\n" "$pkgName"
		printf "Installer exit code: %s\n" "$installerExitCode"
		exit 2
	fi

# Cleanup
rm -rf "$downloadDirectory"/"$pkgName"
rm -rf "$choiceFile"

exit 0
