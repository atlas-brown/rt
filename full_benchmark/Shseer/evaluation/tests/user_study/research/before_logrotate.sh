#!/bin/bash
rpath="$(readlink ${BASH_SOURCE})"
if [ -z "$rpath" ];then
    rpath=${BASH_SOURCE}
fi
thisDir="$(cd $(dirname $rpath) && pwd)"
cd "$thisDir"

user="${SUDO_USER:-$(whoami)}"
home="$(eval echo ~$user)"

red=$(tput setaf 1)
green=$(tput setaf 2)
yellow=$(tput setaf 3)
blue=$(tput setaf 4)
cyan=$(tput setaf 5)
        bold=$(tput bold)
reset=$(tput sgr0)
function runAsRoot(){
    verbose=0
    while getopts ":v" opt;do
        case "$opt" in
            v)
                verbose=1
                ;;
            \?)
                echo "Unknown option: \"$OPTARG\""
                exit 1
                ;;
        esac
    done
    shift $((OPTIND-1))
    cmd="$@"
    if [ -z "$cmd" ];then
        echo "${red}Need cmd${reset}"
        exit 1
    fi

    if [ "$verbose" -eq 1 ];then
        echo "run cmd:\"${red}$cmd${reset}\" as root."
    fi

    if (($EUID==0));then
        sh -c "$cmd"
    else
        if ! command -v sudo >/dev/null 2>&1;then
            echo "Need sudo cmd"
            exit 1
        fi
        sudo sh -c "$cmd"
    fi
}
###############################################################################
# write your code below (just define function[s])
# function with 'function' is hidden when run help, without 'function' is show
###############################################################################
# TODO
install(){
    local defaultDest=$home/.logrotate
    local dest=${1:-$defaultDest}
    echo "logrotate dest: $dest"
    if [ ! -d "$dest" ];then
        echo "mkdir $dest..."
        mkdir -p $dest
    fi
    cat<<EOF > ${dest}/logrotate.conf
#/tmp/testfile.log {
    #weekly | monthly | yearly
    # Note: size will override weekly | monthly | yearly
    #size 100k # | size 200M | size 1G

    #rotate 3
    #compress

    # Note: copytruncate conflics with create
    # and copytruncate works well with tail -f,create not works well with tail -f
    #create 0640 user group
    #copytruncate

    #su root root
#}
EOF
    cat<<EOF2
Tips:
    add settings to ${dest}/logrotate.conf
    use logrotate -d ${dest}/logrotate.conf to check configuration file syntax
    add "logrotate -s ${dest}/status ${dest}/logrotate.conf" to crontab(Linux) or launchd(MacOS)
EOF2
}



###############################################################################
# write your code above
###############################################################################
function help(){
    cat<<EOF2
Usage: $(basename $0) ${bold}CMD${reset}

${bold}CMD${reset}:
EOF2
    perl -lne 'print "\t$1" if /^\s*(\w+)\(\)\{$/' $(basename ${BASH_SOURCE}) | grep -v runAsRoot
}

case "$1" in
     ""|-h|--help|help)
        help
        ;;
    *)
        "$@"
esac
