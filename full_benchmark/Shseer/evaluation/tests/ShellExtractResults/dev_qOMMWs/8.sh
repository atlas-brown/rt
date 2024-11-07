apt-get install -y zsh && wget https://github.com/robbyrussell/oh-my-zsh/raw/master/tools/install.sh -O - | sh

# Disable auto updates
echo "DISABLE_AUTO_UPDATE=\"true\"" >> ~/.zshrc
