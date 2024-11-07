#!/bin/bash

# You need GO and Terraform installed for this to work.

source ./scripts/variables/bashVar.sh

# Install Terraform plugin
# mkdir src repo directory
if [ -d "${GOPATH}${gitPath}" ]; then
  echo "${GOPATH}${gitPath} allredy exist"
else
  echo "Make GO src dir"
  mkdir -p ${GOPATH}${gitPath};
fi

# Download src repo
if [ -d "${GOPATH}${gitPath}${pluginDir}/.git" ]; then
  echo "Git repo allredy exist"
  echo "Cd to git repo and check for updates"
  cd ${GOPATH}${gitPath}${pluginDir} && git pull
else
  echo "Cd to git repo"
  cd ${GOPATH}${gitPath}
  echo "Clone git repo"
  git clone ${gitUrl}
fi

# Build from src repo
echo "Change to git repo dir"
cd ${GOPATH}${gitPath}${pluginDir}

echo "Make terraform libvirt plugin"
 make install

echo "Copy plugin to Terraform folder"
cp ${GOBIN}${pluginDir} ${HOME}${terraformPath}