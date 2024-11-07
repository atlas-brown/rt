#!/bin/bash

if command -v fzf > /dev/null 2>&1 ; then
    SELECTOR=\fzf
elif command -v peco > /dev/null 2>&1 ; then
    SELECTOR=\peco
else
    SELECTOR=
fi

whichbin() {
    local command_path

    if [ -e /etc/debian_version ] || [ -e /etc/debian_release ]; then
        command_path=$(\which "$1" 2> /dev/null)
    elif [ -e /etc/fedora-release ] || [ -e /etc/redhat-release ]; then
        command_path=$(\which --skip-alias "$1" 2> /dev/null)
    else
        echo "${FUNCNAME[0]}: unknown distribution" 1>&2
        return 22
    fi

    local result=$?
    if [ "$result" -ne 0 ]; then
        echo "no ${1} in (${PATH})" 1>&2
        return $result
    fi

    readlink -f "$command_path"
}

# Convert datetime to an epoch time.
#
# example: a datetime to an epoch time
#     $ date2epoch "2017-01-01 00:00:00+0900"
#     1483196400
#
# example: show current epoc time
#     $ date2epoch
#     1493254466
date2epoch() {
    if [ "$1" != "" ]; then
        \date +%s -d "$1"
    else
        \date +%s
    fi
}

# Convert an epoch time to a datetime
#
# example:
#     $ epoch2date 1483196400
#     2017-01-01 00:00:00+09:00
epoch2date() {
    if [ "$1" = "" ]; then
        echo "Usage: ${FUNCNAME[0]} EPOCH_TIME" 1>&2
        return 22
    fi

    \date -d @"$1" --rfc-3339=seconds
}

# find files in a directory with exclude hidden files/directories
ff() {
    local path=$1
    local name_pattern=$2

    if [ "$path" = "" ]; then
        echo "Usage: ${FUNCNAME[0]} DIR_PATH" 1>&2
        return 22
    fi

    if [ "$name_pattern" = "" ]; then
        \find "$path" -not -path '*/\.*' -type f
    else
        \find "$path" -not -path '*/\.*' -type f -name "$name_pattern"
    fi
}

# find directories in a directory with exclude hidden directories
fd() {
    local path=$1
    local name_pattern=$2

    if [ "$path" = "" ]; then
        echo "Usage: ${FUNCNAME[0]} DIR_PATH" 1>&2
        return 22
    fi

    if [ "$name_pattern" = "" ]; then
        \find "$path" -not -path '*/\.*' -type d
    else
        \find "$path" -not -path '*/\.*' -type d -name "$name_pattern"
    fi
}

# find files and grep file name with exclude hidden files/directories
ffg() {
    if [ $# -ne 2 ]; then
        echo "Usage: ${FUNCNAME[0]} ROOT_DIR PATTERN" 1>&2
        return 22
    fi

    ff "$1" | \grep -E --ignore-case "$2"
}

psgrep() {
    local pattern=$1
    local psaux

    psaux=$(\ps aux)

    if [ "$pattern" = "" ]; then
        echo "Usage: ${FUNCNAME[0]} PATTERN" 1>&2
        return 22
    fi

    echo -e "$psaux" | \head -1
    echo -e "$psaux" | \grep -E "$pattern"
}

pssort() {
    local sort_key=$1

    if \ps aux --sort "${sort_key}" > /dev/null 2>&1 ; then
        local stdout
        stdout=$(\ps aux --sort "${sort_key}")
        echo -e "${stdout}"
    else
        local header
        header=$(echo -e "$(\ps aux)" | \head -1)
        echo "invalid sort key. valid sort keys are:" ${header,,} 1>&2
        return 1
    fi
}

extract() {
    local archive_file=$1

    if [ ! -f "${archive_file}" ]; then
        echo "'${archive_file}' is not a valid file to extract" 1>&2
        return 1
    fi

    case "${archive_file}" in
        *.tar.bz2) \tar -xvf "${archive_file}"    ;;
        *.tar.gz)  \tar -xvf "${archive_file}"    ;;
        *.tar.xz)  \tar -xvf "${archive_file}"    ;;
        *.bz2)     \bunzip2 "${archive_file}"     ;;
        *.gz)      \gunzip "${archive_file}"      ;;
        *.tar)     \tar -xvf "${archive_file}"    ;;
        *.tbz2)    \tar -jxvf "${archive_file}"   ;;
        *.tgz)     \tar -zxvf "${archive_file}"   ;;
        *.zip)     \unzip "${archive_file}"       ;;
        *.ZIP)     \unzip "${archive_file}"       ;;
        *) echo "'${archive_file}' cannot be extracted via extract()" 1>&2; return 2 ;;
    esac
}

lsarchive() {
    local archive_file=$1

    if [ ! -f "${archive_file}" ]; then
        echo "'${archive_file}' is not a valid file to extract" 1>&2
        return 1
    fi

    case "${archive_file}" in
        *.tar.bz2) \tar -ztvf "${archive_file}"  ;;
        *.tar.gz)  \tar -ztvf "${archive_file}"  ;;
        *.tar.xz)  \tar -ztvf "${archive_file}"  ;;
        *.tar)     \tar -ztvf "${archive_file}"  ;;
        *.tgz)     \tar -ztvf "${archive_file}"  ;;
        *.whl)     \unzip -l "${archive_file}"  ;;
        *.zip)     \unzip -l "${archive_file}"  ;;
    esac
}

# list up installed packages
lspkg() {
    if [ -e /etc/debian_version ] || [ -e /etc/debian_release ]; then
        dpkg --list
    elif [ -e /etc/fedora-release ] || [ -e /etc/redhat-release ]; then
        rpm -qa
    else
        echo "unknown distribution" 1>&2
        return 1
    fi
}

listpkg() {
    for command in $(compgen -c | sort); do
        bin_path=$(whichbin "$command" 2> /dev/null)
        if [ "$?" -ne 0 ]; then
            continue
        fi

        package=$(whichpkg "$bin_path" 2> /dev/null)
        if [ "$?" -ne 0 ]; then
            continue
        fi

        if [ -e /etc/debian_version ] || [ -e /etc/debian_release ]; then
            echo "$package"
        elif [ -e /etc/fedora-release ] || [ -e /etc/redhat-release ]; then
            echo "$package: $bin_path"
        else
            echo "unknown distribution" 1>&2
            return 1
        fi
    done
}

# find a package which includes a specified command
whichpkg() {
    local command=$1
    local command_path
    local result
    local package

    if [ "${command}" = "" ]; then
        echo "Usage: ${FUNCNAME[0]} COMMAND" 1>&2
        return 22
    fi

    command_path=$(whichbin "${command}")
    result=$?
    if [ "$result" -ne 0 ]; then
        return $result
    fi

    if [ -e /etc/debian_version ] || [ -e /etc/debian_release ]; then
        package=$(dpkg -S "$command_path")
    elif [ -e /etc/fedora-release ] || [ -e /etc/redhat-release ]; then
        package=$(rpm -qf "$command_path")
    else
        echo "unknown distribution" 1>&2
        return 1
    fi

    result=$?
    if [ "$result" -ne 0 ]; then
        echo "file ${command_path} is not owned by any package"
        return $result
    fi

    echo "$package"
}

ccat() {
    pygmentize -O style=monokai -f console256 -g "$1"
}

cless() {
    pygmentize -O style=monokai -f console256 -g "$1" | less
}

# select a directory and change current directory to the directory
cdp() {
    if ! command -v "$SELECTOR" > /dev/null 2>&1; then
        echo "${FUNCNAME[0]}: require fzf|peco" 1>&2
        return 1
    fi

    dst_dir=$(\ls -d */ */*/ | sed 's/\/$//g' | $SELECTOR)
    if [ "$dst_dir" = "" ]; then
        return 1
    fi

    \pushd ${dst_dir} > /dev/null
}

ffgp() {
    if ! command -v "$SELECTOR" > /dev/null 2>&1; then
        echo "${FUNCNAME[0]}: require fzf|peco" 1>&2
        return 1
    fi

    less $(ffg . $1 | $SELECTOR)
}


lastmodified() {
    local dir_path

    dir_path=$(readlink -f "$1")
    if [ "${dir_path}" = "" ]; then
        echo "Usage: ${FUNCNAME[0]} DIR_PATH" 1>&2
        return 22
    fi

    \find "$dir_path" -type d -name '.*' -prune -o -type f -printf '%TY-%Tm-%TdT%TH:%TM %p\n' | sort
}


histgrep() {
    if [ "$1" = "" ]; then
        if ! command -v "$SELECTOR" > /dev/null 2>&1; then
            echo "Usage: ${FUNCNAME[0]} DIR_PATH" 1>&2
            return 22
        fi

        command=$(history | sort --reverse --numeric-sort | $SELECTOR | awk '{c="";for(i=3;i<=NF;i++) c=c $i" "; print c}')
        echo "$command"

        return 0
    fi

    history | \grep -E "$1" | uniq --skip-fields 2
}

histexec() {
    command=$(history | sort --reverse --numeric-sort | $SELECTOR |  awk '{c="";for(i=3;i<=NF;i++) c=c $i" "; print c}')
    $command
}

if command -v python > /dev/null 2>&1; then
    httpserver() {
        local port=$1
        local ipaddr

        ipaddr=$(ifdata -pa $(route | \grep "^default" | awk '{print $8}' | uniq))
        python3 -m http.server --bind "$ipaddr" "${port:-8888}"
    }
fi

default_ip_a() {
    ifdata -pa $(route | \grep -E '^default|^0\.0\.0\.0' | awk '{print $8}' | uniq)
}


# find files and grep file name with exclude hidden files/directories
fetch_gh_tarball_sha256() {
    if [ $# -ne 1 ]; then
        echo "Usage: ${FUNCNAME[0]} owner/repo" 1>&2
        return 22
    fi

    REPO_ID=$1
    URL="https://api.github.com/repos/$REPO_ID/releases/latest"
    TAG_NAME=$(curl -sSL "$URL" | jq -er .tag_name)

    if [ "$?" != "0" ]; then
        echo "failed to fetch tag_name from $URL" 1>&2
        return 2
    fi

    echo "https://github.com/$REPO_ID/archive/${TAG_NAME}.tar.gz"
    curl -sL https://github.com/$REPO_ID/archive/${TAG_NAME}.tar.gz | openssl sha256 -r
}
