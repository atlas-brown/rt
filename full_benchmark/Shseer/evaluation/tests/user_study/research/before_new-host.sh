#!/bin/bash

set -eux

if [[ ! -d ~/.common-configs ]]; then
  git clone --recurse-submodules https://github.com/programmablereya/common-configs.git ~/.common-configs
  cd ~/.common-configs
else
  cd ~/.common-configs
  git pull
fi

source ./bash_aliases.sh

./install.sh

if [[ ! -f ~/.ssh/id_ed25519.pub ]]; then
  ssh-keygen -o -a 100 -t ed25519 -f ~/.ssh/id_ed25519

  ssh-authorize-key ~/.ssh/id_ed25519.pub

  echo "*** New keypair generated. Please add the new public key to github/bitbucket authorized keys:"
  cat ~/.ssh/id_ed25519.pub
  read -p "Press ENTER when done."
fi

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
