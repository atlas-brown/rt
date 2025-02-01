# Changing/making/removing directory
setopt auto_pushd
setopt pushd_ignore_dups
setopt pushdminus

alias -g ...='../..'
alias -g ....='../../..'
alias -g .....='../../../..'
alias -g ......='../../../../..'

alias -- -='cd -'
alias 1='cd -1'
alias 2='cd -2'
alias 3='cd -3'
alias 4='cd -4'
alias 5='cd -5'
alias 6='cd -6'
alias 7='cd -7'
alias 8='cd -8'
alias 9='cd -9'

alias md='mkdir -p'
alias rd=rmdir

function d () {
  if [[ -n $1 ]]; then
    dirs "$@"
  else
################################################################################
# Commit message: style: use `-n` flag in `head` and `tail` commands (#10391)  Co-authored-by: Marc Cornellà <hello@mcornella.com>
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/e86c6f5e7fc9f024a427e2870ab70644b5454725
# Category: about refactor
# Notes: 
# Changed content:
# -     dirs -v | head -10
# +     dirs -v | head -n 10
################################################################################
# put stream annotation here
# stream enable
    dirs -v | head -10
  fi
}
compdef _dirs d

# List directory contents
alias lsa='ls -lah'
alias l='ls -lah'
alias ll='ls -lh'
alias la='ls -lAh'