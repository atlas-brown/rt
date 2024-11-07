#!/bin/bash

alias reload!='. ~/.zshrc'
alias reset!="cd $DOTFILES && ./bootstrap.sh"
alias cls='clear' # Good 'ol Clear Screen command

alias h="cd ~"
alias ..="cd .."
alias ...="cd ../.."
alias ....="cd ../../.."
alias cd..="cd .."

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -

alias :q="exit"
alias q="exit"
alias ch="history -c && > ~/.bash_history"
alias path='printf "%b\n" "${PATH//:/\\n}"'
alias ll="ls -l"
alias la="ls -la"
alias m="man"

# Gets the current ip address
alias ip="dig +short myip.opendns.com @resolver1.opendns.com"

# fdfind -> fd as short binary is taken
alias fd="fdfind"

# months
alias months='locale mon | sed '\''s/;/\n/g'\'' | awk '\''{ print NR, $1 }'\'' | fzf'

# Project and Site shortcuts
alias p='cd $(fd . $(echo "${PROJECTS//:/ }") | fzf --ansi -1)'
alias s='cd $(fd . $(echo "${SITES//:/ }") | fzf --ansi -1)'

# Capture takes over the std ouput of a process
capture() {
    sudo dtrace -p "$1" -qn '
        syscall::write*:entry
        /pid == $target && arg0 == 1/ {
            printf("%s", copyinstr(arg1, arg2));
        }
    '
}
