#!/bin/zsh
# 
# Make the dirstack more persistant
# 
# Run dirpersiststore in ~/.zlogout

dirpersiststore () {
################################################################################
# Commit message: Escape &'s in path name.  Need to find general function for escaping all shell metacharacters.
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/21e2a913bff765b8dc23f12309059f7446e0ff99
# Category: 
# Notes: 
# Changed content:
# -     dirs -p | sed 's/ /\\ /g;s/^/pushd -q /;1!G;h;$!d;' > ~/.zdirstore
# + # FIXME: need to escape all shell metacharacters, not just spaces!
# +     dirs -p | sed 's/ /\\ /g;s/&/\\&/;s/^/pushd -q /;1!G;h;$!d;' > ~/.zdirstore
################################################################################
# put stream annotation here
# stream enable
    dirs -p | sed 's/ /\\ /g;s/^/pushd -q /;1!G;h;$!d;' > ~/.zdirstore
}

dirpersistrestore () {
    if [ -f ~/.zdirstore ]; then
        source ~/.zdirstore
    fi
}

DIRSTACKSIZE=10
setopt autopushd pushdminus pushdsilent pushdtohome pushdignoredups
dirpersistrestore

# Make popd changes permanent without having to wait for logout
alias popd="popd;dirpersiststore"