#!/bin/bash

set -e
set -o pipefail

echo "Starting installation"

#export DEBIAN_FRONTEND=noninteractive
#echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
apt-get update && apt-get install -y --no-install-recommends apt-utils


apt-get update && apt-get -y -q --no-install-recommends install \
    apt-utils \
    autoconf \
    automake \
    build-essential \
    clang-7 \
    curl \
    dialog \
    fontconfig \
    g++ \
    gdb \
    git \
    gzip \
    iputils-ping \
    locales \
    net-tools \
    openssh-server \
    pkg-config \
    pyflakes \
    pyflakes3 \
    python \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    python3-setuptools \
    tmux \
    unzip \
    wget \
    zip \
    zsh

echo ">Installed main packages!\n"

locale-gen en_US en_US.UTF-8
dpkg-reconfigure locales
update-locale LANG=en_US.UTF-8
source /etc/default/locale
export LANG=en_US.UTF-8

if [[ -n $LOCAL_INSTALLATION ]]; then
    # alacritty dependencies
    apt-get update && apt-get -y -q --no-install-recommends install \
        libfontconfig1-dev \
        libxcb-render0-dev \
        libxcb-shape0-dev \
        libxcb-xfixes0-dev \
        libxcb1-dev
    echo ">Installed alacritty dependencies"
fi

#yes | add-apt-repository ppa:mmstick76/alacritty

apt-get update
#apt-get -y -q --no-install-recommends install \
#    alacritty

echo ">Installed alacritty!\n"

apt-get install -y --reinstall ca-certificates
mkdir -p /usr/local/share/ca-certificates/cacert.org
wget -P /usr/local/share/ca-certificates/cacert.org http://www.cacert.org/certs/root.crt http://www.cacert.org/certs/class3.crt
update-ca-certificates --fresh
export SSL_CERT_DIR=/etc/ssl/certs

echo ">Installed certificates!\n"

# Dirty hack, sometimes base image already has newer cmake installed manually

curl -sLO https://github.com/BurntSushi/ripgrep/releases/download/13.0.0/ripgrep_13.0.0_amd64.deb
dpkg -i ripgrep_13.0.0_amd64.deb
rm ripgrep_13.0.0_amd64.deb

echo ">Installed ripgrep!\n"

if [ ! -f "/usr/bin/cmake" ]; then
    apt-get update && apt-get -y -q install cmake
fi

echo ">Installed basic tools"

cd ${HOME}

if [ ! -d "${SCRIPT_PATH}" ]; then
    git clone https://github.com/f-squirrel/scripts.git
fi
cd ${SCRIPT_PATH}
git checkout ${TARGET_BRANCH}
cd ..

# Need GH for lsp-installer
wget --quiet --no-check-certificate https://github.com/cli/cli/releases/download/v2.5.1/gh_2.5.1_linux_amd64.deb
dpkg -i gh_2.5.1_linux_amd64.deb
rm gh_2.5.1_linux_amd64.deb
#TODO: add condition for GUI!
#bash ${SCRIPT_PATH}/deployment/common/fonts.sh
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/JetBrains/JetBrainsMono/master/install_manual.sh)"

bash ${SCRIPT_PATH}/deployment/common/setup_links.sh
bash ${SCRIPT_PATH}/deployment/common/setup_zshrc.sh
bash ${SCRIPT_PATH}/deployment/common/setup_custom_script_helpers.sh

bash ${SCRIPT_PATH}/deployment/ubuntu/nvim_core.sh
bash ${SCRIPT_PATH}/deployment/ubuntu/nvim_gui.sh
# fzf needs to be installed after zsh because it patches .zshrc
bash ${SCRIPT_PATH}/deployment/ubuntu/build_tools.sh
bash ${SCRIPT_PATH}/deployment/common/install_vim_plugins.sh

wget --quiet --no-check-certificate https://github.com/sharkdp/bat/releases/download/v0.15.4/bat_0.15.4_amd64.deb
dpkg -i bat_0.15.4_amd64.deb
rm bat_0.15.4_amd64.deb

echo "installation completed"
