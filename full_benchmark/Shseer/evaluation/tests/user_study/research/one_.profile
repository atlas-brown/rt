#!/bin/bash

if [ "$(cat "$HOME"/.MUID)" = a57a753581205757ac302383c1a6b2f686a84356941c17d4eea95a227d6a25dc ] 
then 
		export MACHINE_NAME="D"; 
fi


if [ "$(cat "$HOME"/.MUID)" = a57a753581205757ac302383c1a6b2f686a84356941c17d4eea95a227d6a25dc ] 
then 
		echo "eq" ; 
fi

if [ "$(cat "$HOME"/.MUID)" = aca16920583e42bdcf5fc70618f55b6a ]
then 
		export MACHINE_NAME="M"; 
fi

if [ "$(cat "$HOME"/.MUID)" = a57a753581205757ac302383c1a6b2f686a84356941c17d4eea95a227d6a25dc ] 
then 
		echo "eq" ; 
fi

# env vars
export GOPATH="$HOME"/go
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8


# make less more friendly for non-text input files, see lesspipe(1)
[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# set variable identifying the chroot you work in (used in the prompt below)
if [ -z "${debian_chroot:-}" ] && [ -r /etc/debian_chroot ]; then
    debian_chroot=$(cat /etc/debian_chroot)
fi

# disable CTRL-D terminating terminal
set -o ignoreeof

if [ -f "$HOME"/.bash_aliases ]; then
    source "$HOME"/.bash_aliases
fi

if [ -f "$HOME"/.shrc_customised ]; then
    source "$HOME"/.shrc_customised
fi

# nvim back folder
[ ! -d "$HOME"/.vim/backup/ ] && mkdir -p "$HOME"/.vim/backup/ 
[ ! -d "$HOME"/.vim/swap/   ] && mkdir -p "$HOME"/.vim/swap/   
[ ! -d "$HOME"/.vim/undo/   ] && mkdir -p "$HOME"/.vim/undo/   

# fuck 
command -v fuck >/dev/null && eval "$(thefuck --alias)"

# conda
#eval "$(register-python-argcomplete conda)" # it does not work

if [ "x$MACHINE_NAME" = "xD" ]
then
	echo "Have a good time";
fi

# for visual studio code
export DOTNET_CLI_TELEMETRY_OPTOUT=1

# for my binaries
PATH=$PATH:"$HOME"/bin:"$HOME"/.local/bin

export WORKON_HOME="$HOME"/.virtualenvs
# virtualenv and virtualenvwrapper
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
[ -f /usr/local/bin/virtualenvwrapper.sh ] && source /usr/local/bin/virtualenvwrapper.sh
[ -f /usr/bin/virtualenvwrapper.sh ] && source /usr/bin/virtualenvwrapper.sh

export GPG_TTY=$(tty)
export KEYTIMEOUT=1
export BASH_ENV=~/.vim_bash_env
export CLASSPATH=".:/usr/local/lib/antlr-4.8-complete.jar:$CLASSPATH"
if [ -e /home/v/.nix-profile/etc/profile.d/nix.sh ]; then . /home/v/.nix-profile/etc/profile.d/nix.sh; fi # added by Nix installer
