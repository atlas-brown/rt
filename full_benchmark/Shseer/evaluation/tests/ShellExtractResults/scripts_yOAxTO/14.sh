#!/bin/sh

set -eo pipefail

echo "Started nvim-plug setup!"

sh -c 'curl -fLo "${XDG_DATA_HOME:-$HOME/.local/share}"/nvim/site/autoload/plug.vim --create-dirs \
       https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim'

echo "Installed Vim-Plug"

# Install nodejs to enable LSPs
curl -sL https://deb.nodesource.com/setup_17.x -o nodesource_setup.sh
bash nodesource_setup.sh
apt -y -q --no-install-recommends install nodejs
rm nodesource_setup.sh

set +e
npm install uuid@latest
set -e

echo "Installed NodeJs"

set +e
nvim -e -u ~/.config/nvim/init.vim -i NONE -c "PlugInstall $(nproc)" \
    -c "sleep 120" \
    -c "qa"
# Install all Tree-sitter plugins
nvim -e -u ~/.config/nvim/init.vim -i NONE -c "TSUpdateSync" \
    -c "sleep 220" \
    -c "qa"

nvim -e -u ~/.config/nvim/init.vim -i NONE \
    -c ":LspInstall --sync clangd" \
    -c ":LspInstall --sync cmake" \
    -c ":LspInstall --sync grammarly" \
    -c ":LspInstall --sync pyright" \
    -c ":LspInstall --sync rust_analyzer" \
    -c ":LspInstall --sync bashls" \
    -c "sleep 120" \
    -c "qa"
set -e

echo "Installed nvim plugins"

cd ${HOME}

echo "Finished plugin setup!\n"
