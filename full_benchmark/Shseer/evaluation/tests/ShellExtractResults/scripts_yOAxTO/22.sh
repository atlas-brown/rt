#!/bin/env bash

set -e

CURL_FLAGS="--silent --show-error --fail --location"
WGET_FLAGS="--quiet"

function check_prerequisites {
    if command -v curl &> /dev/null ; then
        echo "Curl found"
        return 0
    elif command -v wget &> /dev/null ; then
        echo "Wget found"
        return 0
    fi
    echo "Neither curl nor wget installed"
    return 1
}

function download {
    local link=${1}
    local output=${2}

    if command -v curl &> /dev/null ; then
        curl ${CURL_FLAGS} ${link} --output ${output}
    elif command -v wget &> /dev/null ; then
        wget ${WGET_FLAGS} ${link} --output-document ${output}
    fi
}

function install_nvim {
    echo "Installing Neovim"
    local nvim_install_path=${HOME}/.local/bin/nvim
    mkdir -p "$(dirname "${nvim_install_path}")"

    download \
        'https://github.com/neovim/neovim/releases/latest/download/nvim.appimage' \
        ${nvim_install_path}
    chmod u+x ${nvim_install_path}

    # The OS supports FUSE
    if command -v fusermount &> /dev/null ; then
        echo "Neovim installed to ${nvim_install_path}."
    else
        cd $(dirname "${nvim_install_path}")
        ${nvim_install_path} --appimage-extract &> /dev/null
        rm ${nvim_install_path}
        mv squashfs-root nvim_root
        ln -s nvim_root/AppRun ${nvim_install_path}
        cd -
        echo "Neovim installed to ${nvim_install_path}."
    fi

    if ! echo ${PATH} | grep "${HOME}\/\.local\/bin" &> /dev/null ; then
        echo "The install dir is not in your PATH, add it to make nvim available"
        if [[ $(basename ${SHELL}) == "zsh" ]] ; then
            echo "echo 'export PATH=${HOME}/.local/bin/:${PATH}' >> ~/.zshrc"
            echo "source ~/.zshrc"
        else
            echo "echo 'export PATH=${HOME}/.local/bin/:${PATH}' >> ~/.bashrc"
            echo "source ~/.bashrc"
        fi
    fi
    echo "To remove it, simply rm -r ${nvim_install_path}*"
}

function print_help {
    echo "This script installs minimal Vim/Neovim config and creates backup for existing configs"
    echo "Options:"
    echo "--help       - Show help"
    echo "--install    - Install Neovim"
    echo "--insecure   - Tell curl to ignore certificate issues, should not be a problem since the script downloads from Github"
}

function print_restore_commands {
    local backup_path=${1}
    local config_path=${2}
    if [ -z "${backup_path}" ]; then
        echo "In order to remove the settings run:"
        echo "rm ${config_path}"
    else
        echo "In order to restore the original settings run:"
        echo "mv ${backup_path} ${config_path}"
    fi
}

function main {
    if [[ "$*" == *"--help"* ]]; then
        print_help
        exit 0
    fi
    if [[ "$*" == *"--insecure"* ]]; then
        echo "insecure"
        CURL_FLAGS="${CURL_FLAGS} --insecure"
        WGET_FLAGS="${WGET_FLAGS} --no-check-certificate"
    fi

    if ! check_prerequisites ; then
        exit 1
    fi

    if [[ "$*" == *"--install"* ]]; then
        install_nvim
        config_path="${HOME}/.config/nvim/init.vim"
        mkdir -p "$(dirname "${config_path}")"
    else
        if command -v nvim &> /dev/null ; then
            echo "Found Neovim"
            config_path="${HOME}/.config/nvim/init.vim"
            mkdir -p "$(dirname "${config_path}")"
        elif command -v vim &> /dev/null ; then
            echo "Found Vim"
            config_path="${HOME}/.vimrc"
        else
            echo "Failed to find Neovim or Vim, please install either of them to continue"
            echo "To install a non-intrusive version of Neovim, run this script with --install"
            exit 1
        fi
    fi

    if [ -f "${config_path}" ]; then
        backup_path="${config_path}.$(date --iso-8601=seconds).origin"
        mv "${config_path}" "${backup_path}"
        echo "Created backup for user config in ${backup_path}"
    fi

    download \
        'https://raw.githubusercontent.com/f-squirrel/scripts/master/dotfiles/vim/minimal.vim' \
        "${config_path}"
    echo "Installed config to ${config_path}"

    print_restore_commands ${backup_path} ${config_path}
}

main "$@"
