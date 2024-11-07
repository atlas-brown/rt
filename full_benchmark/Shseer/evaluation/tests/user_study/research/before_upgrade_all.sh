#!/bin/bash
# MIT License

# Copyright (c) 2020 johnkramorbhz

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
dt=$(date '+%d %h %Y %H:%M:%S');
echo "INFO: Hello there, $USER@$HOSTNAME!"
echo "INFO: Script started at $dt"
echo -e "INFO: Getting info about your OS\c"
unameOut="$(uname -s)"
OSID=$(cat /etc/os-release | grep -w "ID")
OSLIKE=$(cat /etc/os-release | grep -w "ID_LIKE")
echo -e "\e[32m done \e[0m"
echo "INFO: Your OS type string: $unameOut, OSID: $OSID, OSLIKE: $OSLIKE"
echo -e "INFO: Are you running this script as root or sudo? \c"
if [[ $EUID -ne 0 ]]; then
   echo -e "\e[31mNo \e[0m"
   echo "ERROR: This script must be run as root since it installs some packages necessary for deployment"
   echo "INFO: Restart it as 'sudo $0 $1 $2' instead" 
   exit 1
else
echo -e "\e[32mYes \e[0m"
fi
if [ "$OSID" = "ID=ubuntu" ] || [ "$OSID" = "ID=debian" ] || [ "$OSLIKE" = "ID_LIKE=debian" ]; then
curl -sL https://deb.nodesource.com/setup_14.x | bash -
apt update -y
apt upgrade -y
apt install nodejs
# Update snap packages
snap refresh
# Upgrade all pip3 packages
pip3 list --outdated --format=freeze | grep -v '^\-e' | cut -d = -f 1 | xargs -n1 pip3 install -U 
else
echo "ERROR: Your distribution is not supported"
exit 1
fi