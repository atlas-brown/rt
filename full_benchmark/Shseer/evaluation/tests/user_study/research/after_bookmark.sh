#!/bin/bash
#
# Auth: Ryan Y
#
# Mimics the bookmark function in iron python
# terminals, to store a database of folders I
# can jump to.

debug=0

if [[ -n $(which nvim) ]]
then
    editor='nvim'
else
    editor='vi'
fi
bookmark_file="${HOME}/.fs-bookmarks"
var_file="${HOME}/.fs-vars"
if [[ ! -f ${bookmark_file} ]]
then
    echo Creating $bookmark_file
    touch $bookmark_file
fi
if [[ ! -f ${var_file} ]]
then
    echo Creating $var_file
    touch $var_file
fi

##########################
# PARSE OPTIONAL ARGUMENTS
##########################
let LIST=0
let DELETE_ALL=0
let VAR=0
let EDIT=0

POSITIONAL=()
while [[ $# -gt 0 ]]
do
    key="$1"

    case $key in
    -l|--list)
        let LIST=1
        shift # past argument
        ;;
    -s|--var|-v|--symbol)
        let VAR=1
        shift # past argument
        ;;
    --delete-all)
    let DELETE_ALL=1
    shift # past argument
    ;;
    -e|--edit)
    let EDIT=1
    shift # past argument
    ;;
    -d|--delete)
    DELETE="$2"
    shift # past argument
    shift # past value
    ;;
    *)    # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
    esac
done

set -- "${POSITIONAL[@]}" # restore positional parameters

###################################
## ECHO COMMANDS SO USER CAN SEE ##
###################################

if (($DELETE_ALL == 1)) || (($LIST == 1)) || [[ -n $DELETE ]] && (($debug == 1))
then
    echo "LIST           = ${LIST}"
    echo "DELETE         = ${DELETE}"
fi

function show_bookmarks()
{
        echo ---------------------------------------- | lolcat
        printf '\tAvailable bookmarks' | lolcat
        echo ---------------------------------------- | lolcat
        cat $bookmark_file | sed 's/\<alias\>//g' | sed 's/cd //g' | sed 's/=/\t=>\t/g' | sed 's/#SEP/----------------------------------------/'
        #cat $bookmark_file
        echo refreshing bookmarks and variables...
        source $bookmark_file
        source $var_file
}

#####################
## PERFORM ACTIONS ##
#####################
if (($LIST == 1))
then
    if [[ -n $(cat $bookmark_file) ]]
    then
        show_bookmarks
    fi
elif (($EDIT == 1))
then
    $editor $bookmark_file $var_file
elif (($DELETE_ALL == 1))
then
    echo Deleting entire bookmark list
    cp $bookmark_file ${bookmark_file}.bak
    echo "" > $bookmark_file
elif [[ -n $DELETE ]]
then
    echo Deleting ${DELETE^^} from $bookmark_file
    delete_awk_program="\$1 != ${DELETE^^} {print \$0}"
    cp $bookmark_file ${bookmark_file}.bak
    cat $bookmark_file | awk -F '[ =]{1,2}' "$delete_awk_program" > $bookmark_file
    unalias ${1^^p} &> /dev/null
elif (($VAR == 1))
then
    bookmark_name=${1:-""}
    if [[ -n $var_name ]]
    then
        echo Adding $1 to $var_file
        var=${2:-$(pwd)}
        echo "${var_name^^}='$var'" >> $var_file
        source $var_file
    else
        echo ---------------------------------------- | lolcat
        printf '\tAvailable variables' | lolcat
        echo ---------------------------------------- | lolcat
        cat $var_file | sed 's/\<export\>//g' | sed 's/cd //g' | sed 's/=/\t=>\t/g'
    fi
else
    bookmark_name=${1:-""}
    if [[ -n $bookmark_name ]]
    then
        echo Adding $1 to $bookmark_file
        bookmark_location=${2:-$(pwd)}
        echo "alias ${bookmark_name^^}='cd $bookmark_location'" >> $bookmark_file
        echo "export ${bookmark_name^^}='$bookmark_location'" >> $var_file
        source $bookmark_file
        source $var_file
    else
        show_bookmarks
    fi
fi
