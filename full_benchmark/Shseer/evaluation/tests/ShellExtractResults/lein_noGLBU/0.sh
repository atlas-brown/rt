#!/bin/bash

#######################################################
##### CONSTANTS
#######################################################
OS=linux
ARCH=x86_64
SRC_DIR=src/native/
BIN_DIR=target/bin/
SRC_PATH=${SRC_DIR}$OS/$ARCH/
BIN_PATH=${BIN_DIR}$OS/$ARCH/
##### available user commands
CMD_BUILD=build
CMD_CLEAN=clean

#######################################################
##### VARIABLES
#######################################################
COMMAND=${1:-build}

#######################################################
##### FUNCTIONS
#######################################################
validate_inputs(){
  # check global "inputs" e.g. env variables
  if [ -z "$JAVA_HOME" ] && [ -d "$JAVA_HOME" ]; then
    echo JAVA_HOME not set, exiting
    exit 1
  fi
}

setup(){
  # create directory to hold compiled code
  if [ ! -d "$BIN_PATH" ]; then
    mkdir -p "$BIN_PATH"
  fi
}

##### command functions
build(){
  # compile
  g++ "$SRC_PATH/MyNative.c" -I "$JAVA_HOME/include" -I "$JAVA_HOME/include/linux" -l ncurses -shared -o "$BIN_PATH/libMyNative.so" -fPIC
}

clean(){
  rm -rf "$BIN_DIR"
}

#######################################################
##### LOGIC
#######################################################
validate_inputs
setup
eval $COMMAND
