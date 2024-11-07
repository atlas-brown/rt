#!/bin/sh

apt-get install -y jq

# Security
apt-get install -y netcat-openbsd

# Fixes
apt-get install -y zsh
wget https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh -O - | zsh

# Disable auto updates
echo "DISABLE_AUTO_UPDATE=\"true\"" >> ~/.zshrc

(
  cd ~ 
  git init .
  git fetch
  git reset origin/master --hard
)
