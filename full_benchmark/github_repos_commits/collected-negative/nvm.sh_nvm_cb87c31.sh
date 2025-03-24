#!/usr/bin/env bash
################################################################################
# Commit message: 
# Commit URL: https://github.com/nvm-sh/nvm/commit/cb87c313a9eaa2a9b7301aa0abaed0dc9d93cd01
# Category: 
# Notes: 
# Changed content:
# - ls "$NVM_DIR" | grep -v src
# + ls "$NVM_DIR" | grep -v src | grep -v nvm.sh
################################################################################
# @output "~(.*(src|nvm\.sh).*)"
      ls "$NVM_DIR" | grep -v src | grep -v nvm.sh