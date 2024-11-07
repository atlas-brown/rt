#!/bin/bash

# Update base tools
apt-get update

# Major development tools
apt-get install -y build-essential git-core git

# Useful core command-line utilities
apt-get install -y coreutils bsdmainutils

# Core dependencies
apt-get install -y wget curl

# Colored command-line utils
apt-get install -y colordiff
