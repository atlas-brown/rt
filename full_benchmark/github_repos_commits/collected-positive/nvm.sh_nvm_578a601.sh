#!/usr/bin/env bash
################################################################################
# Commit message: Filter out of `nvm ls` things that start with a dot. Fixes #421, closes #422.
# Commit URL: https://github.com/nvm-sh/nvm/commit/578a601b2702bd1cae43f0cbc68a42849809a85c
# Category: 
# Notes: 
# Changed content:
# - | sort -t. -u -k 1.2,1n -k 2,2n -k 3,3n`
# + | sort -t. -u -k 1.2,1n -k 2,2n -k 3,3n | grep -v '^ *\.'`
################################################################################
# node has version numbers of the form 'v0.12.13' and 'v22.14.0' etc
# @output "~( *\..*)"
    find "$NVM_DIR/" -maxdepth 1 -type d -name "$(nvm_format_version $PATTERN)*" -exec basename '{}' ';' | sort -t. -u -k 1.2,1n -k 2,2n -k 3,3n