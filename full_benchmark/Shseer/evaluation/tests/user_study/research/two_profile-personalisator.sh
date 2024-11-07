#!/usr/bin/env bash

PACKAGE_URL=https://github.com/mrachuta/dev-null/raw/master/profile-files.tar
arch_name=$(echo $PACKAGE_URL | rev | cut -d'/' -f 1 | rev)
folder_name=$(echo "$arch_name" | rev | cut -d'.' -f 2 | rev)
curr_datetime=$(date +%Y-%m-%d-%H_%M_%S)

get_package() {

  echo "Downloading package with pre-configured files..."

  wget -O "/tmp/$arch_name" $PACKAGE_URL
  mkdir "/tmp/$folder_name"
  tar -xvf "/tmp/$arch_name" -C "/tmp/$folder_name"

  echo "Package downloaded!"
}

configure_bashrc() {

  echo "bashrc configuration..."
  echo "Backup of .bashrc available in /home/$1/bashrc-$curr_datetime"

  cp "/home/$1/.bashrc" "/home/$1/bashrc-$curr_datetime.bak"
  echo "Chosing random color for machine-name background..."
  # Last color in table is 256, but after 229 there are
  # gray/black/white colours 
  # https://misc.flogisoft.com/bash/tip_colors_and_formatting
  color_code=$(( RANDOM % 229 ))
  echo "$color_code"
  searched_val="D_MACHINE_COLOR=\"\\\e\[30;48;5;[[:digit:]]{1,3}m\""
  new_val="D_MACHINE_COLOR=\"\\\e\[30;48;5;${color_code}m\""
  sed -i -r "s~^$searched_val~$new_val~" "/tmp/$folder_name/.bashrc"
  chmod 644 "/home/$1/bashrc-$curr_datetime.bak"
  chown "$1":"$1" "/home/$1/bashrc-$curr_datetime.bak"
  cp "/tmp/$folder_name/.bashrc" "/home/$1/.bashrc"
  chmod 644 "/home/$1/.bashrc"
  chown "$1":"$1" "/home/$1/.bashrc"

  echo "bashrc configuration finished!"

}

configure_bash_aliases() {
  
  echo "bash_aliases configuration..."

  cp "/tmp/$folder_name/.bash_aliases" "/home/$1/.bash_aliases"
  chmod 644 "/home/$1/.bash_aliases"
  chown "$1":"$1" "/home/$1/.bash_aliases"

  echo "bash_aliases configuration finished"
}

configure_vim() {

  # Good source
  # https://vimawesome.com/

  plugin_list=(
    "https://github.com/luochen1990/rainbow"
    "https://github.com/martinda/jenkinsfile-vim-syntax"
    "https://github.com/ekalinin/dockerfile.vim"
    "https://github.com/python-mode/python-mode"
    "https://github.com/scrooloose/nerdcommenter"
    "https://github.com/itchyny/lightline.vim"
    "https://github.com/pangloss/vim-javascript"
    "https://github.com/chr4/nginx.vim"
  )

  echo "Configuring vim..."

  cp "/tmp/$folder_name/.vimrc" "/home/$1/.vimrc"
  chmod 644 "/home/$1/.vimrc"
  chown "$1":"$1" "/home/$1/.vimrc"

  # Install pathogen
  mkdir -p "/home/$1/.vim/autoload" "/home/$1/.vim/bundle" "/home/$1/.vim/colors"
  curl -LSso "/home/$1/.vim/autoload/pathogen.vim" "https://tpo.pe/pathogen.vim"

  # Install molokai theme
  wget -P "/home/$1/.vim/colors" \
    "https://github.com/tomasr/molokai/raw/master/colors/molokai.vim"

  # Install molokayo theme
  wget -P "/home/$1/.vim/colors" \
    "https://github.com/fmoralesc/molokayo/raw/master/colors/molokayo.vim"

  # Install plugins
  # Do not change!
  plugin_list_len=${#plugin_list[@]}

  for i in $(seq 0 $((plugin_list_len - 1))); do
    plugin_name=$(echo "${plugin_list[$i]}" | rev | cut -d'/' -f 1 | rev)
    echo "Installing plugin: $plugin_name"
    cd "/home/$1/.vim/bundle" && git clone "${plugin_list[$i]}"
  done

  chown -R "$1":"$1" "/home/$1/.vim"

  echo "Vim configuration finished!"
}

usage() {

  echo -e "Script for personalisation bash & other tools\n"
  echo "Usage: profile-personalisator.sh user"
  echo "Replace 'user' with your username"

}

main() {

  usage

  if [[ -n "$1" ]]; then
    get_package
    configure_bashrc "$1"
    configure_bash_aliases "$1"
    configure_vim "$1"
    echo "Run 'source ~/.bashrc' to see the changes"
  else
    usage
  fi
}

main "$1"
