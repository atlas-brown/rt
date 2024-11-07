#!/bin/sh

set -eo pipefail

if [ -d "${HOME}/.oh-my-zsh" ]; then
    exit 0
fi
printf "Started zshrc setup!\n"
cd ${HOME}
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
echo "Installed zsh: " $?

sed -i 's/ZSH_THEME="robbyrussell"/ZSH_THEME="miloshadzic"/' ${HOME}/.zshrc

# Make C-P/C-N behave as up/down

echo 'bindkey "^P" up-line-or-beginning-search' >> ${HOME}/.zshrc
echo 'bindkey "^N" down-line-or-beginning-search' >> ${HOME}/.zshrc

# language setup
echo 'export LANG=en_US.UTF-8' >> ${HOME}/.zshrc
echo 'export LC_CTYPE=en_US.UTF-8' >> ${HOME}/.zshrc
echo 'export LC_ALL=en_US.UTF-8' >> ${HOME}/.zshrc

echo "export EDITOR='nvim'" >> ${HOME}/.zshrc

# to show user when in ssh
echo 'DEFAULT_USER=$USER' >> ${HOME}/.zshrc
echo "alias view='nvim -R'" >> ${HOME}/.zshrc

echo "alias gdb='gdb --tui'" >> ${HOME}/.zshrc

# To search for hidden files

echo "export FZF_CTRL_T_COMMAND='rg --files --hidden -g \"\!.git\" '" >> ${HOME}/.zshrc
echo 'export FZF_DEFAULT_COMMAND=${FZF_CTRL_T_COMMAND}' >> ${HOME}/.zshrc

echo "export RIPGREP_CONFIG_PATH=${HOME}/.ripgreprc" >> ${HOME}/.zshrc

#Setup zshrc
if [[ -n $LOCAL_INSTALLATION ]]; then
    echo 'export REMOTE_DEV_USER=<user name for remote dev station>' >> ${HOME}/.zshrc
    echo 'export REMOTE_DEV_SERVER=<IP>' >> ${HOME}/.zshrc
    echo 'export MIN_PORT=7780' >> ${HOME}/.zshrc
    echo 'export MAX_PORT=7790' >> ${HOME}/.zshrc
    echo 'export NVIM_QT_PATH="<path neovim-qt>"' >> ${HOME}/.zshrc

    # To allow crash dumps
    # Probably you need to setup core pattern
    echo 'ulimit -c unlimited' >> ${HOME}/.zshrc

    echo "Please fill the env variable added to ${HOME}/.zshrc"
fi
chsh -s $(which zsh)

printf "Finished zshrc setup!\n"
