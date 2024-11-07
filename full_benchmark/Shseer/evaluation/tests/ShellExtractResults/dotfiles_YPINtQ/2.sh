#!/bin/sh

# Remvoe DS_Storee from folder
alias remove-DSstore='find . -name *.DS_Store -type f -delete'

# Re-generate right-click menu
alias clean-openwith='/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -kill -r -domain local -domain system -domain user'

# Convert Disc to ISO
#
# usage :  convert-disc2iso image.iso /path/to/source
# eg    :  convert-disc2iso image.iso ~/Desktop/Windows7.iso /Volumes/Windows\ 7\ Install
alias convert-disc2iso='hdiutil makehybrid -iso -joliet -o'

# Show and Remove Browser and System Download History
alias show-dlhistory="sqlite3 ~/Library/Preferences/com.apple.LaunchServices.QuarantineEventsV* 'select LSQuarantineDataURLString from LSQuarantineEvent'"
alias remove-dlhistory="sqlite3 ~/Library/Preferences/com.apple.LaunchServices.QuarantineEventsV* 'delete from LSQuarantineEvent'"

# Show Hide Hidden Files in Finder
alias finder-showhidden='defaults write com.apple.finder ShowAllFiles TRUE'
alias finder-hidehidden='defaults write com.apple.finder ShowAllFiles FALSE'
