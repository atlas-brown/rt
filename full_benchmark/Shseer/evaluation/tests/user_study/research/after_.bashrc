#!/usr/bin/env bash

# If not running interactively, don't do anything
case $- in
	*i*) ;;
	*) return;;
esac

# Path to the bash it configuration
export BASH_IT="$HOME/.bash_it"

# Lock and Load a custom theme file.
# Leave empty to disable theming.
# location /.bash_it/themes/
export BASH_IT_THEME='sexy'

# (Advanced): Change this to the name of your remote repo if you
# cloned bash-it with a remote other than origin such as `bash-it`.
# export BASH_IT_REMOTE='bash-it'

# Your place for hosting Git repos. I use this for private repos.
export GIT_HOSTING='git@git.domain.com'

# Don't check mail when opening terminal.
unset MAILCHECK

# Change this to your console based IRC client of choice.
export IRC_CLIENT='irssi'

# Set this to the command you use for todo.txt-cli
export TODO="t"

# Set this to false to turn off version control status checking within the prompt for all themes
export SCM_CHECK=true

# Set Xterm/screen/Tmux title with only a short hostname.
# Uncomment this (or set SHORT_HOSTNAME to something else),
# Will otherwise fall back on $HOSTNAME.
#export SHORT_HOSTNAME=$(hostname -s)

# Set Xterm/screen/Tmux title with only a short username.
# Uncomment this (or set SHORT_USER to something else),
# Will otherwise fall back on $USER.
#export SHORT_USER=${USER:0:8}

# Set Xterm/screen/Tmux title with shortened command and directory.
# Uncomment this to set.
#export SHORT_TERM_LINE=true

# Set vcprompt executable path for scm advance info in prompt (demula theme)
# https://github.com/djl/vcprompt
#export VCPROMPT_EXECUTABLE=~/.vcprompt/bin/vcprompt

# (Advanced): Uncomment this to make Bash-it reload itself automatically
# after enabling or disabling aliases, plugins, and completions.
# export BASH_IT_AUTOMATIC_RELOAD_AFTER_CONFIG_CHANGE=1

# Uncomment this to make Bash-it create alias reload.
# export BASH_IT_RELOAD_LEGACY=1

# Load Bash It
source "$BASH_IT"/bash_it.sh

# Neovim
alias e="nvim"
export NVIM_CFG="$HOME/.config/nvim/init.vim"
alias cfgnvim="e $NVIM_CFG"
alias re="e -S ./Session.vim"
alias eI="e +PlugInstall +qall"
alias eC="e +PlugClean! +qall"

# Bash
export BASH_CFG="$HOME/.bashrc"
alias cfgbash="e $BASH_CFG"

# Tmux
alias t="tmux"
alias ta="t a -t"
alias tls="t ls"
alias tn="t new -t"

alias q="exit"

# Open xserver
open_xserver () {
	curdir=$(pwd)
	if [ $# -eq 0 ]
	then
		#cd /mnt/c/ProgramData/Microsoft/Windows/Start\ Menu/Programs/Xming/ && cmd.exe /c "Xming.lnk" & echo "" && cd
		cd
		/mnt/c/Program\ Files\ \(x86\)/Xming/XLaunch.exe & echo "X-server is running as default..."
		cd $curdir
	else
		if [ -e $1 ]
		then
			cd
			/mnt/c/Program\ Files\ \(x86\)/Xming/XLaunch.exe -run $1 & echo "X-server is running with '$1' file..."
			cd $curdir
		else
			cd
			echo "There is no: '$1'"
			/mnt/c/Program\ Files\ \(x86\)/Xming/XLaunch.exe & echo "X-server is running as default..."
			cd $curdir
		fi
	fi
}
# Kill xserver
kill_xserver () {
	cmd.exe /c "taskkill /F /IM Xming.exe /IM XLaunch.exe"	
}
# Check xserver
check_xserver () {
	cmd.exe /c "tasklist" | grep "XLaunch.exe\|Xming.exe"
}

# Open pulseaudio
open_pulseaudio () {
	/mnt/c/wsl/bin/pulseaudio.exe &
}
# Kill pulseaudio
kill_pulseaudio () {
	cmd.exe /c "taskkill /F /IM pulseaudio.exe"
}
# Check pulseaudio
check_pulseaudio () {
	cmd.exe /c "tasklist" | grep "pulseaudio.exe"
}

#export REAL_IP=$(dig +noall +answer $(hostname -s) | tail -1 | cut -f 5)
## GUI
#export DISPLAY=$REAL_IP:0
## AUDIO
#export PULSE_SERVER=tcp:$REAL_IP
export DISPLAY=192.168.1.139:0
export PULSE_SERVER=tcp:192.168.1.139
export DISPLAY=192.168.1.139:0
export PULSE_SERVER=tcp:192.168.1.139
