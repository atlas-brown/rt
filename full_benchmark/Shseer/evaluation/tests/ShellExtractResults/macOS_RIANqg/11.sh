#!/bin/bash

# remove sudo timeout

# Make a backup of sudoers file

cp /etc/sudoers{,.bak}

# Verify backup sudoers file
visudo -c -f /etc/sudoers.bak
## add bailout and error message if failed

# Make a working copy of sudoers file
cp /etc/sudoers{,.work}

# Verify working copy of sudoers file
visudo -c -f /etc/sudoers.work
## add bailout and error message if failed

# Modify timeout setting in working copy of sudoers file
chmod u+w /etc/sudoers.work
echo "Defaults timestamp_timeout=0" >> /etc/sudoers.work
chmod u-w /etc/sudoers.work

# Verify working copy of sudoers file
visudo -c -f /etc/sudoers.work
## add bailout and error message if failed

# Replace sudoers file with working copy
mv /etc/sudoers.work /etc/sudoers

# Verify new sudoers file
visudo -c -f /etc/sudoers
## replace with sudoers.bak and error message if failed
