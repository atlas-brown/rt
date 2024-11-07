#!/bin/bash

# Get current com.apple.SoftwareUpdate CatalogURL value

susSetting=$(defaults read /Library/Preferences/com.apple.SoftwareUpdate CatalogURL)

# If CatalogURL is not null, delete the CatalogURL value

if [ -n "$susSetting" ]; then
		defaults delete /Library/Preferences/com.apple.SoftwareUpdate CatalogURL
		echo "CatalogURL value has been deleted"
	else
		echo "CatalogURL was already null"
fi

exit 0
