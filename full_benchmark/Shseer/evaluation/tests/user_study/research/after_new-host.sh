#!/bin/bash

set -eux

if [[ ! -d ~/.common-configs ]]; then
  git clone --recurse-submodules https://github.com/programmablereya/common-configs.git ~/.common-configs
  cd ~/.common-configs
else
  cd ~/.common-configs
  git pull
fi

set +eux
source ./bash_aliases.sh
set -eux

./install.sh

if [[ ! -f ~/.ssh/id_ed25519.pub ]]; then
  ssh-keygen -o -a 100 -t ed25519 -f ~/.ssh/id_ed25519

  ssh-authorize-key ~/.ssh/id_ed25519.pub

  echo "*** New keypair generated. Please add the new public key to github/bitbucket authorized keys:"
  cat ~/.ssh/id_ed25519.pub
  read -s -p "Press ENTER after adding this public key to github/bitbucket authorized keys."
fi

function getCurrentGithubId() {
  local RESULT;
  RESULT=$(ssh -o "IdentitiesOnly=yes" -i ~/.ssh/id_ed25519 -T git@github.com </dev/null 2>&1) || echo "$RESULT" >&2; exit 1
  USERNAME=$(echo "$RESULT" | sed -n 's/^Hi \([^!]\+\)! You'"'"'ve successfully authenticated, but GitHub does not provide shell access\.$/Successfully authenticated to GitHub as \1/; T; p') || exit 1
  echo "$USERNAME"
  [[ -n "$USERNAME" ]];
}

READING=true
while "$READING" && ! RESULT=$(getCurrentGithubId) || [[ $RESULT != 'programmablereya' ]]; do
  read -p "Press ENTER after adding this public key to github/bitbucket authorized keys, or enter 'no' to skip this step: " FROM_ME_DAWG
  if [[ 'no' == "$FROM_ME_DAWG" ]]; then
    READING=false
  fi
done

ORIGIN=$(git ls-remote --get-url origin)
if [[ "$ORIGIN" != 'git@github.com:programmablereya/common-configs.git' ]]; then
  git remote set-url origin git@github.com:programmablereya/common-configs.git
fi

GITMAIL=$(git config --get user.email || true)
GITUSER=$(git config --get user.name || true)
if [[ "$GITMAIL" != 'mstaib.git@reya.zone' ]] || [[ "$GITUSER" != 'Mari' ]]; then
  git config user.email 'mstaib.git@reya.zone'
  git config user.name 'Mari'
fi

sync_git_only
