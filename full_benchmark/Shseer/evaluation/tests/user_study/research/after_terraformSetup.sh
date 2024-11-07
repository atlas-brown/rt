#!/bin/bash

export PATH=$PATH:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin:/usr/local/go/bin
source ./scripts/vars/bashVar.sh

# Install Terraform plugin
#su ${SUDO_USER}
mkdir -p ${GOPATH}/src/github.com/dmacvicar;
cd ${GOPATH}/src/github.com/dmacvicar
#sudo -u ${SUDO_USER} 
git clone https://github.com/dmacvicar/terraform-provider-libvirt.git
cd $GOPATH/src/github.com/dmacvicar/terraform-provider-libvirt
echo $PATH
#which go
#echo $?
pwd
#sudo -u jea 
make install