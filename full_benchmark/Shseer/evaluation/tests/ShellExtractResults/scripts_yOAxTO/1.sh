#!/bin/bash

ROOT_DIR=$HOME
SRC="/Volumes/Macintosh HD/Users/skyjack/Pictures/iPhoto Library.photolibrary/"
DST="$ROOT_DIR/Cloud@Mail.Ru/photo/iPhoto Library.photolibrary/"
APPS_TO_CHECK=("iPhoto" "Aperture")

SUCCESS_COLOR=2
ERROR_COLOR=1
MESSAGE_COLOR=4

log() {
    echo $(tput setaf ${1})"$(date)" - "$2"
}

log_success() {
    log ${SUCCESS_COLOR} "$1"
}

log_error() {
    log ${ERROR_COLOR} "$1"
}

log_message() {
    log ${MESSAGE_COLOR} "$1"
}

run_rsync() {
    log_message "Starting rsync"

    local src="${1}"
    local dst="${2}"

    rsync -rah --delete --progress --human-readable "${src}" "${dst}"

    if [[ $? == 0 ]]; then
        log_success "Rsync finished successfully"
    else
        log_error "Rsync FAILED"
    fi
}

is_process_running() {
    local number=$(ps xc | grep "$1" | wc -l)

    if [ $number -gt 0 ]; then
    	echo TRUE
    else
    	echo FALSE
    fi
}

check_prerequisites() {

    for application in "${APPS_TO_CHECK[@]}"
    do
        :
        local res="$(is_process_running "$application")"

        if [ "$res"  == "TRUE" ] ; then
            log_error "Cannot rsync: '$application' is running"
            exit
        fi
    done

}

main() {

    check_prerequisites

    run_rsync "${SRC}" "${DST}"
}

main $@
