#---oh-my-zsh plugin : task Autocomplete for Jake tool---
# Jake : https://github.com/mde/jake
# Warning : Jakefile should have the right case : Jakefile or jakefile
# Tested on : MacOSX 10.7 (Lion), Ubuntu 11.10
# Author : Alexandre Lacheze (@al3xstrat)
# Inspiration : http://weblog.rubyonrails.org/2006/3/9/fast-rake-task-completion-for-zsh 

function _jake () {
################################################################################
# Commit message: Jake-node plugin : update - remove the need to write a `jake_tasks` in the directory - use most recent usage of completion with zsh - tested for MacOSX and Ubuntu
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/31badac2ea2ecdc77cf4c339fcef9472940cb261
# Category: 
# Notes: 
# Changed content:
# -   if [ -f Jakefile ]; then
# -     if _jake_does_task_list_need_generating; then
# -       echo "\nGenerating .jake_tasks..." > /dev/stderr
# -       jake -T | cut -d " " -f 2 | sed -E "s/.\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]//g" > .jake_tasks
# -     fi
# -     reply=( `cat .jake_tasks` )
# +   if [ -f Jakefile ]||[ -f jakefile ]; then
# +     compadd `jake -T | cut -d " " -f 2 | sed -E "s/.\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]//g"`
################################################################################
# put stream annotation here
# stream enable
  if [ -f Jakefile ]||[ -f jakefile ]; then
    compadd `jake -T | cut -d " " -f 2 | sed -E "s/.\[([0-9]{1,2}(;[0-9]{1,2})?)?[m|K]//g"`
  fi
}

compdef _jake jake