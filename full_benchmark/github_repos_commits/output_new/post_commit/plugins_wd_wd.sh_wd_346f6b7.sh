#!/bin/zsh

# WARP DIRECTORY
# ==============
# Jump to custom directories in terminal
# because `cd` takes too long...
#
# @github.com/mfaerevaag/wd


## variables
readonly CONFIG=$HOME/.warprc

# colors
readonly BLUE="\033[96m"
readonly GREEN="\033[92m"
readonly YELLOW="\033[93m"
readonly RED="\033[91m"
readonly NOC="\033[m"


## init

# check if config file exists
if [ ! -e $CONFIG ]
then
    # if not, create config file
    touch $CONFIG
fi

# load warp points
typeset -A points
while read -r line
do
    arr=(${(s,:,)line})
    key=${arr[1]}
    val=${arr[2]}

    points[$key]=$val
done < $CONFIG


## functions

wd_warp()
{
    local point=$1

    if [[ $point =~ "^\.+$" ]]
    then
        if [ $#1 < 2 ]
        then
            wd_print_msg $YELLOW "Warping to current directory?"
        else
            (( n = $#1 - 1 ))
            cd -$n > /dev/null
        fi
    elif [[ ${points[$point]} != "" ]]
    then
        cd ${points[$point]}
    else
        wd_print_msg $RED "Unknown warp point '${point}'"
    fi
}

wd_add()
{
################################################################################
# Commit message: [wd] v0.3.1: Improved completion and bug fixes
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/346f6b7d24d6021efa8c5167088f98c10f00ad3f
# Category: 
# Notes: 
# Changed content:
# -     if [[ $2 =~ "^\.+$" || $2 =~ "^\s*$" ]]
# +     local force=$1
# +     local point=$2
# + 
# +     if [[ $point =~ "^[\.]+$" ]]
# +     then
# +         wd_print_msg $RED "Warp point cannot be just dots"
# +     elif [[ $point =~ "(\s|\ )+" ]]
################################################################################
# put stream annotation here
# stream enable
    local force=$1
    local point=$2

    if [[ $point =~ "^[\.]+$" ]]
    then
        wd_print_msg $RED "Warp point cannot be just dots"
    elif [[ $point =~ "(\s|\ )+" ]]
    then
################################################################################
# Commit message: [wd] v0.3.1: Improved completion and bug fixes
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/346f6b7d24d6021efa8c5167088f98c10f00ad3f
# Category: 
# Notes: 
# Changed content:
# -         wd_print_msg $RED "Illegal warp point (see README)."
# -     elif [[ ${points[$2]} == "" ]] || $1
# +         wd_print_msg $RED "Warp point should not contain whitespace"
# +     elif [[ $point == *:* ]]
################################################################################
# put stream annotation here
# stream enable
        wd_print_msg $RED "Warp point should not contain whitespace"
    elif [[ $point == *:* ]]
    then
################################################################################
# Commit message: [wd] v0.3.1: Improved completion and bug fixes
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/346f6b7d24d6021efa8c5167088f98c10f00ad3f
# Category: 
# Notes: 
# Changed content:
# -         wd_remove $2 > /dev/null
# -         print "$2:$PWD" >> $CONFIG
# +         wd_print_msg $RED "Warp point cannot contain colons"
# +     elif [[ $point == "" ]]
# +     then
# +         wd_print_msg $RED "Warp point cannot be empty"
# +     elif [[ ${points[$2]} == "" ]] || $force
# +     then
# +         wd_remove $point > /dev/null
# +         printf "%q:%q\n" "${point}" "${PWD}" >> $CONFIG
# + 
################################################################################
# put stream annotation here
# stream enable
        wd_print_msg $RED "Warp point cannot contain colons"
    elif [[ $point == "" ]]
    then
        wd_print_msg $RED "Warp point cannot be empty"
    elif [[ ${points[$2]} == "" ]] || $force
    then
        wd_remove $point > /dev/null
        printf "%q:%q\n" "${point}" "${PWD}" >> $CONFIG

        wd_print_msg $GREEN "Warp point added"
    else
        wd_print_msg $YELLOW "Warp point '${point}' already exists. Use 'add!' to overwrite."
    fi
}

wd_remove()
{
    local point=$1

################################################################################
# Commit message: [wd] v0.3.1: Improved completion and bug fixes
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/346f6b7d24d6021efa8c5167088f98c10f00ad3f
# Category: 
# Notes: 
# Changed content:
# - wd_show()
# - {
# -     wd_print_msg $BLUE "Warp points to current directory:"
# -     wd_list_all | grep $PWD$
# - }
# - 
################################################################################
# put stream annotation here
# stream enable
    if [[ ${points[$point]} != "" ]]
    then
        if sed -i.bak "s,^${point}:.*$,,g" $CONFIG
        then
            wd_print_msg $GREEN "Warp point removed"
        else
            wd_print_msg $RED "Something bad happened! Sorry."
        fi
    else
        wd_print_msg $RED "Warp point was not found"
    fi
}

wd_list_all()
{
    wd_print_msg $BLUE "All warp points:"

    while IFS= read -r line
    do
        if [[ $line != "" ]]
        then
            arr=(${(s,:,)line})
            key=${arr[1]}
            val=${arr[2]}

            printf "%20s  ->  %s\n" $key $val
        fi
################################################################################
# Commit message: [wd] v0.3.1: Improved completion and bug fixes
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/346f6b7d24d6021efa8c5167088f98c10f00ad3f
# Category: 
# Notes: 
# Changed content:
# -     done < $CONFIG
# +     done <<< $(sed "s:${HOME}:~:g" $CONFIG)
# + }
# + 
# + wd_show()
# + {
# +     local cwd=$(print $PWD | sed "s:^${HOME}:~:")
# + 
# +     wd_print_msg $BLUE "Warp points to current directory:"
# +     wd_list_all | grep -e "${cwd}$"
################################################################################
# put stream annotation here
# stream enable
    done <<< $(sed "s:${HOME}:~:g" $CONFIG)
}

wd_show()
{
    local cwd=$(print $PWD | sed "s:^${HOME}:~:")

    wd_print_msg $BLUE "Warp points to current directory:"
    wd_list_all | grep -e "${cwd}$"
}

wd_print_msg()
{
################################################################################
# Commit message: [wd] v0.3.1: Improved completion and bug fixes
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/346f6b7d24d6021efa8c5167088f98c10f00ad3f
# Category: 
# Notes: 
# Changed content:
# -     if [[ $1 == "" || $2 == "" ]]
# +     local color=$1
# +     local msg=$2
# + 
# +     if [[ $color == "" || $msg == "" ]]
################################################################################
# put stream annotation here
# stream enable
    local color=$1
    local msg=$2

    if [[ $color == "" || $msg == "" ]]
    then
        print " ${RED}*${NOC} Could not print message. Sorry!"
    else
        print " ${color}*${NOC} ${msg}"
    fi
}

wd_print_usage()
{
################################################################################
# Commit message: [wd] v0.3.1: Improved completion and bug fixes
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/346f6b7d24d6021efa8c5167088f98c10f00ad3f
# Category: 
# Notes: 
# Changed content:
# -     print "Usage: wd [add|-a|--add] [rm|-r|--remove] [ls|-l|--list] <point>"
# -     print "\nCommands:"
# -     print "\t add \t Adds the current working directory to your warp points"
# -     print "\t add! \t Overwrites existing warp point"
# -     print "\t rm \t  Removes the given warp point"
# -     print "\t show \t Outputs warp points to current directory"
# -     print "\t ls \t Outputs all stored warp points"
# -     print "\t help \t Show this extremely helpful text"
# +     cat <<- EOF
# + Usage: wd [add|-a|--add] [rm|-r|--remove] <point>
# + 
# + Commands:
# + 	add	Adds the current working directory to your warp points
# + 	add!	Overwrites existing warp point
# + 	rm	Removes the given warp point
# + 	show	Outputs warp points to current directory
# + 	ls	Outputs all stored warp points
# + 	help	Show this extremely helpful text
# + EOF
################################################################################
# put stream annotation here
# stream enable
    cat <<- EOF
Usage: wd [add|-a|--add] [rm|-r|--remove] <point>

Commands:
	add	Adds the current working directory to your warp points
	add!	Overwrites existing warp point
	rm	Removes the given warp point
	show	Outputs warp points to current directory
	ls	Outputs all stored warp points
	help	Show this extremely helpful text
EOF
}


## run

# get opts
args=$(getopt -o a:r:lhs -l add:,rm:,ls,help,show -- $*)

# check if no arguments were given
if [[ $? -ne 0 || $#* -eq 0 ]]
then
    wd_print_usage

# check if config file is writeable
elif [ ! -w $CONFIG ]
then
    # do nothing
    # can't run `exit`, as this would exit the executing shell
    wd_print_msg $RED "\'$CONFIG\' is not writeable."

else
    for o
    do
        case "$o"
            in
            -a|--add|add)
                wd_add false $2
                break
                ;;
            -a!|--add!|add!)
                wd_add true $2
                break
                ;;
            -r|--remove|rm)
                wd_remove $2
                break
                ;;
            -l|--list|ls)
                wd_list_all
                break
                ;;
            -h|--help|help)
                wd_print_usage
                break
                ;;
            -s|--show|show)
                wd_show
                break
                ;;
            *)
                wd_warp $o
                break
                ;;
            --)
                break
                ;;
        esac
    done
fi

## garbage collection
# if not, next time warp will pick up variables from this run
# remember, there's no sub shell

unset wd_warp
unset wd_add
unset wd_remove
unset wd_show
unset wd_list_all
unset wd_print_msg
unset wd_print_usage

unset args
unset points
unset val &> /dev/null # fixes issue #1