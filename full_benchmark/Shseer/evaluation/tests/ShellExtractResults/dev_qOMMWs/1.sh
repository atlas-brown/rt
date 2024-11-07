#!/bin/bash
#hash 261eba739cc084af6102c891cd58bce15c168b77
(
  cd ~ 
  git init .
  git remote add origin https://github.com/kwketh/dotfiles.git
  git fetch
  git reset origin/master --hard
)
