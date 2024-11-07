#!/bin/bash  
#=================================================================================== 
# 
# Installs Optional software for Linux From Scratch 9.0 on a Red Hat based distribution of 
# linux, such as Fedora, CentOS, or RHEL. 
# Copyright (C) 2019 
 
# This program is free software: you can redistribute it and/or modify 
# it under the terms of the GNU Affero General Public License as published 
# by the Free Software Foundation, either version 3 of the License, or 
# (at your option) any later version. 
 
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
# GNU Affero General Public License for more details. 
 
# You should have received a copy of the GNU Affero General Public License 
# along with this program.  If not, see <https://www.gnu.org/licenses/> 
# 
#===================================================================================

# Sudo-1.8.27 || allows a user to run some (or all) commands as root || 0.4 SBUs
tar xvf sudo-1.8.27.tar.gz
cd sudo-1.8.27
./configure --prefix=/usr              \
            --libexecdir=/usr/lib      \
            --with-secure-path         \
            --with-all-insults         \
            --with-env-editor          \
            --docdir=/usr/share/doc/sudo-1.8.27 \
            --with-passprompt="[sudo] password for %p: " &&
make
read -p "Press [Enter] key to resume..."
make install &&
ln -sfv libsudo_util.so.0.0.0 /usr/lib/sudo/libsudo_util.so.0
read -p "Press [Enter] key to resume..."
cat > /etc/sudoers.d/sudo << "EOF"
Defaults secure_path="/usr/bin:/bin:/usr/sbin:/sbin"
%wheel ALL=(ALL) ALL
EOF
cd /sources
rm -Rf sudo-1.8.27

# wget-1.20.3 || Contains a utility for downloading files from the Web || 0.4 SBUs
tar xvf wget-1.20.3.tar.gz
cd wget-1.20.3
./configure --prefix=/usr      \
            --sysconfdir=/etc  \
            --with-ssl=openssl &&
make
read -p "Press [Enter] key to resume..."
make install
read -p "Press [Enter] key to resume..."

cd /sources
rm -Rf wget-1.20.3

# GPM-1.20.7 || contains a mouse server for the console and xterm || 0.1 SBUs
tar xvf gpm-1.20.7.tar.bz2
cd gpm-1.20.7
sed -i -e 's:<gpm.h>:"headers/gpm.h":' src/prog/{display-buttons,display-coords,get-versions}.c &&
patch -Np1 -i ../gpm-1.20.7-glibc_2.26-1.patch &&
./autogen.sh                                &&
./configure --prefix=/usr --sysconfdir=/etc &&
make
read -p "Press [Enter] key to resume..."
make install                                          &&

install-info --dir-file=/usr/share/info/dir           \
             /usr/share/info/gpm.info                 &&

ln -sfv libgpm.so.2.1.0 /usr/lib/libgpm.so            &&
install -v -m644 conf/gpm-root.conf /etc              &&

install -v -m755 -d /usr/share/doc/gpm-1.20.7/support &&
install -v -m644    doc/support/*                     \
                    /usr/share/doc/gpm-1.20.7/support &&
install -v -m644    doc/{FAQ,HACK_GPM,README*}        \
                    /usr/share/doc/gpm-1.20.7
read -p "Press [Enter] key to resume..."
make install-gpm
read -p "Press [Enter] key to resume..."
cat > /etc/sysconfig/mouse << "EOF"
# Begin /etc/sysconfig/mouse

MDEVICE="/dev/input/mice"
PROTOCOL="imps2"
GPMOPTS=""

# End /etc/sysconfig/mouse
EOF
read -p "Press [Enter] key to resume..."
cd ..
rm -Rf gpm-1.20.7
