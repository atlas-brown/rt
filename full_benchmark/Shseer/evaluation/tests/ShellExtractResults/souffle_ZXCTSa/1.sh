#!/bin/bash

set -e

pushd /mnt/c/ >/dev/null
temp=$(echo `cmd.exe /C 'echo %temp%'` | dos2unix)
random=$(echo `cmd.exe /C 'echo %random%'` | dos2unix)
popd >/dev/null
path="$temp\\$random"
wslpath=`wslpath -u $path`
mkdir $wslpath
echo $wslpath
