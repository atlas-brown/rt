#!/bin/sh

set -eo pipefail

#Powerline for some reason works better when installed manually

#cd
## clone
#git clone https://github.com/powerline/fonts.git --depth=1
## install
#cd fonts
#./install.sh
## clean-up a bit
#cd ..
#rm -rf fonts

#TODO(DD): Optimize the download of only one font

cd ${HOME}
git clone https://github.com/ryanoasis/nerd-fonts.git --depth=1
cd nerd-fonts
./install.sh FiraCode
cd ..
rm -rf nerd-fonts

printf "Finished font setup\n"
