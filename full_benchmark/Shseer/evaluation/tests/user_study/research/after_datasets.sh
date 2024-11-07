#!/bin/bash
################################################################################
## datasets.sh <flag>                                                         ##
## A bash script for mounting/unmounting DATASETS remote directory (hosted on ##
## rpi4) using sshfs / fusermount.                                            ##
##                                                                            ##
## Usage: datasets.sh [options]                                               ##
## Options:                                                                   ##
##    -r <remote>          : set the remote that hosts DATASETS               ##
##    -p <remote_ssh_port> : set ssh port used for accessing remote           ##
##    -m <mount_point>     : set directory where remote DATASETS will be      ##
##                           mounted on                                       ##
##    <flag>               : set either to "on", for mounting remote DATASETS ##
##                           direcotry using sshff, "off" for unmounting it   ##
##                           using fusermount, or leave it empty for getting  ##
##                           the status of mount point                        ##
##                                                                            ##
################################################################################

b=$(tput bold)
n=$(tput sgr0)
red=`tput setaf 1`
green=`tput setaf 2`
reset=`tput sgr0`

# Help function
help(){
    echo "${b}Usage:${n} datasets.sh [-r <remote>] [-p <remote_ssh_port>] [-m <mount_point>] <flag>" 1>&2; exit 1;
}

# Initialize variables
OPTIND=1
DATASETS_IP=192.168.0.28
DATASETS_SSH_PORT=1312
DATASETS_MOUNT_POINT=~/DATASETS/

# Parse command line arguments
while getopts ":r:p:m:" options
do
    case $options in
        r ) DATASETS_IP="$OPTARG"
            ;;
        p ) DATASETS_SSH_PORT="$OPTARG"
            ;;
        m ) DATASETS_MOUNT_POINT="$OPTARG"
            ;;
        * ) help
            ;;
    esac
done
shift $(expr $OPTIND - 1 )

if [[ $# -gt 0 ]]; then
    # A flag has been given
    flag=$1
    if [[ "${flag}" == "on" ]]; then
        echo "Mount datasets..."
        mkdir -p $DATASETS_MOUNT_POINT
        sshfs -p 1312 -C chi@192.168.0.28:/home/datasets/ $DATASETS_MOUNT_POINT -o idmap=user
    elif [[ "${flag}" == "off" ]]; then
        echo "Unmount datasets..."
        fusermount3 -u $DATASETS_MOUNT_POINT
	rm -r $DATASETS_MOUNT_POINT
    else
        echo "${b}${red}[Invalid flag]${reset}${n} Choose:"
        echo " -- ${b}${red}on${reset}${n} (to mount datasets on $DATASETS_MOUNT_POINT),"
        echo " -- ${b}${red}off${reset}${n} (to unmount datasets from $DATASETS_MOUNT_POINT), or "
        echo " -- leave it ${b}${red}empty${reset}${n} for getting current status"
    fi

else
    # No flag has been given -- print status
    mountpoint $DATASETS_MOUNT_POINT >> /dev/null
    status=$?
    if [[ $status -eq 0 ]]; then
        echo "DATASETS is mounted on ${b}${red}$DATASETS_MOUNT_POINT${reset}${n}"
    else
        echo "DATASETS is ${b}${red}not${reset}${n} mounted on ${b}${red}$DATASETS_MOUNT_POINT${reset}${n}"
    fi
fi
