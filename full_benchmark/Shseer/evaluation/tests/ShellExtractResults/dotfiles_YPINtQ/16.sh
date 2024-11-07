#!/bin/sh

alias repo_amend='git commit -a --amend'
alias repo_ca='git commit -a'
alias repo_co='git checkout'
alias repo_history='git log --oneline --abbrev-commit --all --graph --decorate --color'
alias repo_po='git push origin'
alias repo_pu='git push upstream'
alias repo_undo='git reset HEAD~1 --mixed'
alias repo_up='git pull --rebase --prune'
alias repo_squash='git rebase -i'

enable_git_sign() {
  git config gpg.program gpg
  git config commit.gpgsign true
  git config user.signingkey $1
  git config tag.forceSignAnnotated true
}
