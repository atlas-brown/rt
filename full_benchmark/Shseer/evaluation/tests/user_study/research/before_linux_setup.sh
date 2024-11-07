#!/bin/bash -eux

# linux setup
sudo add-apt-repository -y ppa:linrunner/tlp 
sudo add-apt-repository -y ppa:oguzhaninan/stacer 
sudo add-apt-repository -y ppa:gezakovacs/ppa 
sudo add-apt-repository -y ppa:slimbook/slimbook  
sudo apt-add-repository -y ppa:system76-dev/stable 
sudo apt-add-repository -y ppa:teejee2008/ppa
sudo add-apt-repository -y ppa:git-core/ppa 
sudo add-apt-repository -y ppa:obsproject/obs-studio


sudo apt -y install aptitude
sudo aptitude -y update && sudo aptitude -y upgrade



sudo aptitude -y install flatpak
flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo
sudo flatpak install flathub org.linux_hardware.hw-probe
sudo -E flatpak run org.linux_hardware.hw-probe -all -upload
sudo aptitude -y install snapd
sudo aptitude -y install xscreensaver
sudo aptitude -y install clamav clamtk
sudo aptitude -y install asciinema
sudo aptitude -y install festival
sudo aptitude -y install unetbootin
sudo aptitude -y install tlp 
sudo aptitude -y install tlp-rdw
sudo aptitude -y install tldr 
sudo aptitude -y install shotwell
sudo aptitude -y install ffmpeg
sudo aptitude -y install xsel
sudo aptitude -y install nemo
sudo aptitude -y install timeshift
sudo aptitude -y install stacer 
sudo aptitude -y install steam
sudo aptitude -y install slimbookbattery
sudo aptitude -y install gnome-shell-extension-system76-power system76-power
sudo aptitude -y install gparted
sudo aptitude -y install kazam 
sudo aptitude -y install gnome-shell-pomodoro
sudo aptitude -y install obs-studio
sudo aptitude -y install timeshift
sudo aptitude -y install muon
sudo apt -y install openjdk-11-*
sudo aptitude -y install qemu-kvm
sudo adduser jac kvm && sudo chown jac /dev/kvm
sudo aptitude -y install  git git-extras
git config --global user.name "jac"
git config --global user.email joshuacarpentier21@gmail.com

sudo snap install lsd
sudo snap install snap-store

sudo aptitude -y install qemu virt-manager ebtables


git clone https://github.com/usbkey9/uktools && cd uktools
make

sudo aptitude -y install libvirt-bin

sudo aptitude -y install powertop
sudo powertop --calibrate

sudo aptitude -y install ubuntu-restricted-extras




sudo aptitude -y install autoconf-archive gettext valac pkg-config desktop-file-utils appstream-util libappstream-glib-dev libglib2.0-dev gsettings-desktop-schemas-dev gobject-introspection libgirepository1.0-dev libsqlite3-dev libgom-1.0-dev libgstreamer1.0-dev libgtk-3-dev libcanberra-dev libpeas-dev libappindicator3-dev

curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg

sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/microsoft.gpg

sudo sh -c 'echo "deb [arch=amd64] https://packages.microsoft.com/repos/vscode stable main" > /etc/apt/sources.list.d/vscode.list'

sudo aptitude -y update && sudo aptitude -y install code




sudo aptitude -y install ttf-mscorefonts-installer

sudo aptitude -y install fontforge


wget https://gist.github.com/maxwelleite/10774746/raw/ttf-vista-fonts-installer.sh -q -O - | sudo bash

exit 1
























