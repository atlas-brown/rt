#!/bin/sh

# Add a current symlink
export NVM_SYMLINK_CURRENT=true

# Shift directory to /usr/local
export NVM_DIR=/usr/local/nvm
source $(brew --prefix nvm)/nvm.sh

# Fix Paths
PATH=/usr/local/nvm/current/bin:$PATH
export PATH

# Fix Oh-my-zsh plugin error
eval "`npm completion`"
