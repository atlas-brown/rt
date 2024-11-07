#!/bin/bash

git clone https://github.com/bpinto/oh-my-fish.git ~/.oh-my-fish

cd $(dirname $BASH_SOURCE)

mkdir -p ~/.config/fish

ln -sfbv `pwd`/config.fish ~/.config/fish
ln -sfbv `pwd`/functions ~/.config/fish

fish_path=$(which fish)
grep -q "^$fish_path$" /etc/shells || echo $fish_path | sudo tee -a /etc/shells
chsh -s $fish_path
sudo chsh -s $fish_path
