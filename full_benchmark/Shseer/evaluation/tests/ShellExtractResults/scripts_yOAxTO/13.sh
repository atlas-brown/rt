#!/bin/sh

set -eo pipefail

printf "Started link setup!\n"

VIM_DIR_PATH=~/.vim/
mkdir -p ${VIM_DIR_PATH}

NVIM_CONFIG_PATH=~/.config/nvim/
mkdir -p ${NVIM_CONFIG_PATH}

#vim
ln -sf ${HOME}/scripts/dotfiles/vim/.vimrc ${HOME}/.vimrc
ln -sf ${HOME}/scripts/dotfiles/vim/.gvimrc ~/.gvimrc

# nvim
mkdir -p ${NVIM_CONFIG_PATH}
ln -sf ${HOME}/scripts/dotfiles/vim/init.vim ${NVIM_CONFIG_PATH}
ln -sf ${HOME}/scripts/dotfiles/vim/ginit.vim ${NVIM_CONFIG_PATH}

# code style
ln -sf ${HOME}/scripts/dotfiles/vim/code_style/.default_code_style.vim ${VIM_DIR_PATH}/.code_style.vim
printf "Installed default code style to ~/.vim/.code_style.vim\n"
printf "Replace the symlink if needed!\n"


# tmux

if [ ! -d "${HOME}/.tmux/plugins/tpm" ]; then
    git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
fi
ln -sf ${HOME}/scripts/dotfiles/.tmux.conf ~/.tmux.conf
#tmux source-file ~/.tmux.conf

ln -sf ${HOME}/scripts/dotfiles/git/config ~/.gitconfig

ln -sf ${HOME}/scripts/dotfiles/.gdbinit ~/.gdbinit

ALACRITTY_CONFIG_PATH=${HOME}/.config/alacritty
#ln -sf ${HOME}/scripts/dotfiles/alacritty ${ALACRITTY_CONFIG_PATH}
ln -sf ${HOME}/scripts/.ripgreprc ${HOME}/.ripgreprc

printf "Finished link setup!\n"
