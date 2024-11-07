#!/usr/bin/env bash

#  compilefromsource.sh
#  V2RayX
#
#  Created by Cenmrev on 10/15/16.
#  Copyright © 2016 Cenmrev. All rights reserved.

# http://apple.stackexchange.com/questions/50844/how-to-move-files-to-trash-from-command-line
function moveToTrash () {
  local path
  for path in "$@"; do
    # ignore any arguments
    if [[ "$path" = -* ]]; then :
    else
      # remove trailing slash
      local mindtrailingslash=${path%/}
      # remove preceding directory path
      local dst=${mindtrailingslash##*/}
      # append the time if necessary
      while [ -e ~/.Trash/"$dst" ]; do
        dst="`expr "$dst" : '\(.*\)\.[^.]*'` `date +%H-%M-%S`.`expr "$dst" : '.*\.\([^.]*\)'`"
      done
      mv "$path" ~/.Trash/"$dst"
    fi
  done
}

VERSION=$(git describe --tags --always)
PROJECT_ROOT=$(git rev-parse --show-toplevel)

RED='\033[0;31m'
GREEN='\033[0;32m'
BOLD='\033[1m'
NORMAL='\033[0m'
datetime=$(date "+%Y-%m-%dTIME%H%M%S")

useArch=$(uname -m)
if [[ -n "$ARCHS" ]]; then
    useArch="$ARCHS"
fi
if [[ -n "$1" ]]; then
    useArch="$1"
fi

XCODEBUILD_ARGS=(
    -project V2RayXS.xcodeproj 
    -target V2RayXS 
    -configuration Release 
    ARCHS="${useArch}"
)

if [[ ! -f /Applications/Xcode.app/Contents/MacOS/Xcode ]]; then
    echo -e "${RED}Xcode is needed to build V2RayXS, Please install Xcode from App Store!${NORMAL}"
    echo -e "${RED}编译 V2RayXS 需要 Xcode.app，请从 App Store 里安装 Xcode.${NORMAL}"
else
    echo -e "${BOLD}-- Downloading source code --${NORMAL}"
    echo -e "${BOLD}-- 正在下载源码 --${NORMAL}"
    git clone --recursive https://github.com/tzmax/V2RayXS.git "V2RayXS${datetime}"
    cd "V2RayXS${datetime}"
    echo -e "${BOLD}-- Start building V2RayXS --${NORMAL}"
    echo -e "${BOLD}-- 开始编译 V2RayXS --${NORMAL}"
    xcodebuild "${XCODEBUILD_ARGS[@]}"
    if [[ $? == 0 ]]; then
        echo -e "${GREEN}-- Build succeeded --${NORMAL}"
        echo -e "${GREEN}-- 编译成功 --${NORMAL}"
        echo -e "${BOLD}V2RayXS.app: $(pwd)/build/Release/V2RayXS.app${NORMAL}"
    else
        echo -e "${RED}-- Build failed --${NORMAL}"
        echo -e "${RED}-- 编译失败 --${NORMAL}"
    fi
fi


