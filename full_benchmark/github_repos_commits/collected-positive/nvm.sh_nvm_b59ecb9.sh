#!/usr/bin/env bash
################################################################################
# Commit message: Make sure the new `versions` directory is filtered out of nvm_ls output (in zsh).
# Commit URL: https://github.com/nvm-sh/nvm/commit/b59ecb9e11d9e74431b9a7140153d5fe669d13f5
# Category: 
# Notes: 
# Changed content:
# - | sort -t. -u -k 1.2,1n -k 2,2n -k 3,3n | \grep -v '^ *\.' | \grep -e '^v'`
# + | sort -t. -u -k 1.2,1n -k 2,2n -k 3,3n | \grep -v '^ *\.' | \grep -e '^v' | \grep -v -e '^versions$'`
################################################################################
# node has version numbers of the form 'v0.12.13' and 'v22.14.0' etc
# @output "~(versions)"
      find "$(nvm_version_dir new)/" "$(nvm_version_dir old)/" -maxdepth 1 -type d -name "$PATTERN*" -exec basename '{}' ';' | sort -t. -u -k 1.2,1n -k 2,2n -k 3,3n | grep -v '^ *\.' | grep -e '^v'