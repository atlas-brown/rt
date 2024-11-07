#!/bin/bash

#Set Global Variables
set -e
set -u
set -o pipefail

source ${STEP_SHELL_TEMPLATE_SCRIPT}

#Functions

function runArchive() {
   cat ${MOD321_EXPORT_ARCHIVE_TABLES_FILE} |
      while read line; do
         cmnt=$(echo $line | awk '{ print substr($1,0,1) }') #check whether step commented
         if [ "$cmnt" == "#" ]; then
            info_log "Skipping the archive step $line\n"
            continue
         elif [ "$cmnt" == "" ]; then
            info_log "Skipping empty line\n"
         else
            info_log "proceeding with archiving  ${line}"
            bash ${CE_HDLP_S3ARCHIVE_SCRIPT} ${line}
         fi
      done

}

trap clean_up SIGINT SIGHUP SIGTERM EXIT
trap send_failure_email ERR

#Main Program

#CHANGE FOLLOWING VARIABLES ACCORDING TO ENV
return_exit_code=0
#export HDL_ROOT_DIRECTORY_REGEX;
export SA_DEST_DIR
export IM_DEST_DIR
export CM_DEST_DIR
export ARCHIVE_DATE

#Setup new or edit log file.
prepare_log_file

info_log "Command executed: ${0}" 2>&1 | tee -a ${step_log_file}

runArchive 2>&1 | tee -a ${step_log_file}

return_exit_code=$?

error_log " Error code from Archive Procss: ${return_exit_code}" 2>&1 | tee -a ${step_log_file}

exit $return_exit_code
