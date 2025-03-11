#!/bin/bash
# https://stackoverflow.com/questions/49772373/output-of-a-git-command-read-through-shell-script-is-adding-special-characters-w

# ---
# tags: buggy, unclear
# bug:  the '%(color:yellow)' in the format parameter inserts color in the output
#       of the command (which is an escape sequence)
# ---

# i think this can be solved by modeling 'git' and asserting that its output
# should only contain 'normal' characters

# i'd suggest always issuing a warning by default when colors are known
# to be present in the output of a command

git for-each-ref \
    --format='%(align:1,left)%(color:yellow)%(authorname)%(end) %(color:reset)%(refname:strip=3)' \
    --sort=authorname \
    refs/remotes |
    grep test_developer |
    while read line; do
        mystr=${line}
        mybr=${mystr[1]} # color is present here
        git push origin --delete "$mybr" # can't properly read color so complains
    done
