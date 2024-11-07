#!/bin/sh

alias sudo='sudo '

alias ls='ls -Gp'
alias la='ls -la'
alias dir='ls -l'

alias rename='mv '
alias move='mv '

alias cd.='cd ../'                   # Back 1 level
alias cd..='cd ../../'                # Back 2 levels
alias cd...='cd ../../../'             # Back 3 levels
alias cd....='cd ../../../../'          # Back 4 levels
alias cd.....='cd ../../../../../'       # Back 5 levels
alias cd......='cd ../../../../../../'    # Back 6 levels

# Show processes Owned by current user
alias ps-user='ps $@ -u $USER -o pid,%cpu,%mem,start,time,command'
