#!/bin/bash

cd ${HOME}

# XCode utils
xcode-select --install

# Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install.sh)"

brew install \
    cmake \
    bat \
    coreutils \
    git \
    python \
    ripgrep \
    the_silver_searcher \
    tmux \
    wget \
    zsh

cd
git clone https://github.com/f-squirrel/scripts.git
cd ${SCRIPT_PATH}
git checkout ${TARGET_BRANCH}
cd ..


bash ${SCRIPT_PATH}/deployment/common/fonts.sh

bash ${SCRIPT_PATH}/deployment/common/setup_links.sh
bash ${SCRIPT_PATH}/deployment/common/setup_zshrc.sh

# fzf needs to be installed after zsh because it patches .zshrc
bash ${SCRIPT_PATH}/deployment/macos/nvim_core.sh
bash ${SCRIPT_PATH}/deployment/macos/nvim_gui.sh

bash ${SCRIPT_PATH}/deployment/common/setup_custom_script_helpers.sh

bash ${SCRIPT_PATH}/deployment/common/install_vim_plugins.sh
