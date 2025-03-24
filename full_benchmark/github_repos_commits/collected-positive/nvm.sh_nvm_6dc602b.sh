#!/usr/bin/env bash
################################################################################
# Commit message: Ensure that `nvm ls node` doesn't return "node_modules", for example.
# Commit URL: https://github.com/nvm-sh/nvm/commit/6dc602b52117833a552a4688c954a74b663e65f8
# Category: 
# Notes: 
# Changed content:
# - | sort -t. -u -k 1.2,1n -k 2,2n -k 3,3n | \grep -v '^ *\.'`
# + | sort -t. -u -k 1.2,1n -k 2,2n -k 3,3n | \grep -v '^ *\.' | \grep -e '^v'`
################################################################################
# node has version numbers of the form 'v0.12.13' and 'v22.14.0' etc
# @output "v.*"
    find "$NVM_DIR/" -maxdepth 1 -type d -name "$PATTERN*" -exec basename '{}' ';' | sort -t. -u -k 1.2,1n -k 2,2n -k 3,3n | grep -v '^ *\.'