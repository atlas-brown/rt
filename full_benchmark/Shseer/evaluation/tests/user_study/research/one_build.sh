#!/bin/bash

set -e

usage ()
{
    cat <<- _EOF_

#########################################################################################
 Options:
 -h or --help              Display the HELP message and exit.
 --sign_rpms               Enable sign the rpms at the end.  GPG_KEY_ID and GPG_PASSPHRASE
                           must be set in the environment for signing to work
 --spec_name=*             Name of the spec file (Required)
 --build_options=*         Additional options to pass to the rpmbuild command
 --x32                     Add i686 to the build process
 --x64                     Add x86_64 build to the process bit (Default)
_EOF_
}

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd .. && pwd )"

#Validates the params required for running
function validate_params() {

  VARS=('SPEC_NAME')
  for var in "${VARS[@]}"
  do
    if  [ -z  "${!var}"  ]; then
      echo "Please specify the ${var}"
      exit 1
    fi
  done

  #If we want the rpms signed verify GPG_KEY_ID and passphrase given
  if [ "$SIGN_RPMS" = true ]; then
    if [ -z "$GPG_KEY_ID" -o  -z "$GPG_PASSPHRASE" ]; then
      echo "Environment GPG_KEY_ID and GPG_PASSPHRASE required when signing rpms"
      exit
    fi
  fi

}

#Sign rpms
#Expecting the space delimtied list of files or directories to sign
function sign_rpms() {

  # Is parameter #1 zero length (the RPM_FILES)?
  if [ -z "$1" ]
  then
    echo "Expecting RPM Files to sign"
    exit 1
  fi
  RPM_FILES=$1
  for rpm_file in $RPM_FILES
  do
    echo "Signing ${rpm_file} file..."
    #Do the actual signing
    sign_rpm_helper.py --file_path ${rpm_file}
    #Verify signed
    rpm -qpi ${rpm_file} | grep -i "Signature.*Key ID.*${GPG_KEY_ID}"
  done

}

#set default interation
SIGN_RPMS=false
ARCH_ARRAY=()
SPEC_NAME=""
BUILD_OPTIONS=""
for i in "$@"
do
  case $i in
    --build_options=*)
      BUILD_OPTIONS="${i#*=}"
      shift
    ;;
    --sign_rpms)
      SIGN_RPMS=true
      shift
    ;;
    --spec_name=*)
      SPEC_NAME="${i#*=}"
      shift
    ;;
    --x64)
      ARCH_ARRAY+=('x86_64')
      shift
    ;;
    --x32)
      ARCH_ARRAY+=('i686')
      shift
    ;;
    -h | --help)
      usage
      exit
    ;;
    *)
      echo "Unknown option: $i"
      exit 1
    ;;
  esac
done

#Validate params
validate_params

#Ensure our architecture array is unique as user could pass in --x64 and it
#is the default too
if [[ ${ARCH_ARRAY[0]} = "" ]]; then
    ARCH_ARRAY+=('x86_64')
fi
eval ARCH_ARRAY=($(printf "%q\n" "${ARCH_ARRAY[@]}" | sort -u))

for ARCH in "${ARCH_ARRAY[@]}"
do
  RPM_DIR="${ARCH}"
  set -x
  rpmbuild -ba --define '_disable_source_fetch 0' ${BUILD_OPTIONS} --target ${ARCH} SPECS/${SPEC_NAME}
  set +x
  if [ "$SIGN_RPMS" = true ]; then
    sign_rpms "RPMS/${RPM_DIR}/*"
  fi
done
