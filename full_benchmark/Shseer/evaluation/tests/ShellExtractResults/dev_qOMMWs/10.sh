#!/bin/bash
HOSTNAME=dev-env
TAG=latest
DOCKER=docker
WORKDIR=$1
SESSIONID=$(cat /dev/urandom | head -c 256 | md5sum | head -c 8)
FLAGS=""
MOUNTFLAGS=""

if [ -z "$IMAGE" ]; then
    IMAGE_NAME=kwketh/dev-env
    IMAGE=$IMAGE_NAME:$TAG
fi

if [ -z "$NETWORK" ]; then
    NETWORK='bridge'
fi

if [ ! -z "$GITCONFIG" ]; then
    FLAGS="$FLAGS -v \"$GITCONFIG:/root/.gitconfig\""
fi

if [ ! -z "$BASHPROFILE" ]; then
    FLAGS="$FLAGS -v \"$BASHPROFILE:/root/.bash_profile\""
fi

# Set default flags
readonly='false'
mutable='false'

# Parse flags
while getopts 'rnm' flag; do
  case "${flag}" in
    r) readonly='true'; WORKDIR=$2 ;;
    n) network='none'; WORKDIR=$2 ;;
    m) if [ "$readonly" = "true" ]; then
         mutable=true
       else
         echo "error: mutable option can only be used in read-only mode."
         exit
       fi
       ;;
  esac
done

# Convert work directory to full absolute path
if [ -z "$WORKDIR" ]; then
    WORKDIR=$(pwd)
else
    WORKDIR=$(realpath $WORKDIR)
fi

DIRNAME=$(basename $WORKDIR)

if [ "$readonly" = "true" ]; then
    echo "dev-env: running in read-only mode."
    MOUNTFLAGS=":ro"
fi

if [ "$NETWORK" = "none" ]; then
    echo "dev-env: running in no network mode."
fi

if [ "$mutable" = "true" ]; then
    SESSIONDIR="$HOME/.tmp_$SESSIONID"
    echo "         (files are mutable but will be discarded)"
    rsync -a $WORKDIR/ $SESSIONDIR
    WORKDIR="$SESSIONDIR"
    MOUNTFLAGS=""
fi

COMMAND="docker run -h $HOSTNAME --rm -it -w \"/workspace/$DIRNAME\" -v \"$WORKDIR:/workspace/$DIRNAME$MOUNTFLAGS\" $FLAGS --network $NETWORK $IMAGE"

eval $COMMAND

if [ "$mutable" = "true" ]; then
    echo "discarding temporary files."
    rm -rf "$SESSIONDIR"
fi

