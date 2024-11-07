#!/bin/bash

set -e
set -o pipefail

help() {
    echo "Description:"
    echo "The script downloads and installs the development environment"
    echo ""
    echo "Usage:"
    echo "bootstrap.sh [options]"
    echo "Options:"
    echo '-b:   Source branch of the installation script. Default is "master"'
    echo '-r:   Install type "remote"(default value). In this mode none of GUI tools are installed'
    echo '-l:   Install type "local". In this mode GUI tools(neovim-qt, etc) are installed'
    echo ""
    echo "Example:"
    echo "bootstrap.sh -b master -l # Installs master version of dev env for a local setup"
    echo "bootstrap.sh -b master -r # Installs master version of dev env for a remote setup"
}

while getopts "hrlb:" option; do
   case $option in
      h) # display Help
          help
         exit;;
      b) #
         TARGET_BRANCH=$OPTARG
         ;;
      r) #
         export REMOTE_INSTALLATION="remote"
         ;;
      l) #
         export LOCAL_INSTALLATION="local"
         ;;
     \?) # incorrect option
         echo "Error: Invalid option"
         exit;;
   esac
done

export TARGET_BRANCH=${TARGET_BRANCH:-master}

if [[ -n $REMOTE_INSTALLATION && -n $LOCAL_INSTALLATION ]]; then
    printf "Incorrect configuration: both remote(-r) and local(-l) installation flags are set\n"
    help
    exit 1
fi

if [[ -z $LOCAL_INSTALLATION ]]; then
    export REMOTE_INSTALLATION="remote"
    export LOCAL_INSTALLATION=""
fi

if [[ "$OSTYPE" == "linux-gnu" ]]; then
    CURRENT_DISTRO=$(awk -F= '/^NAME/{print $2}' /etc/os-release)
    if [[ "$CURRENT_DISTRO" == "\"Ubuntu\"" ]]; then
        export CURRENT_OS=ubuntu
    else
        echo "Current distro $CURRENT_DISTRO is not supported"
        exit 1
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    export CURRENT_OS=macos
else
    echo "Current OS: $OSTYPE is not supported"
    exit 1
fi

INSTALL_TYPE=${LOCAL_INSTALLATION:-remote}
echo "Build environment with the following settings:"
echo "Installation type:" $INSTALL_TYPE
echo "$LOCAL_INSTALLATION"
echo "$REMOTE_INSTALLATION"
echo "Source branch:" $TARGET_BRANCH
echo "Target OS:" $CURRENT_OS

cd ${HOME}
export SCRIPT_PATH=${PWD}/scripts

if [[ "$CURRENT_OS" == "ubuntu" ]]; then
    # Vanilla Ubuntu comes without curl
    apt-get update && apt-get -y install curl
fi

bash -c "$(curl -fsSL https://raw.githubusercontent.com/f-squirrel/scripts/${TARGET_BRANCH}/deployment/${CURRENT_OS}/install.sh)"
