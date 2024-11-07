#!/bin/bash
#


# Globals
user_name=""
root_pw=""
host_name=""

function set_root_pw() {
	clear
	echo "-----------------"
	echo "| Root Password |"
	echo "-----------------"
	echo
	pass_ok=0
	while [ $pass_ok -eq 0 ]; do
		echo
		echo -n 'Set password for root: '
		read root_pw
		echo -n 'Confirm password for root: '
		read root_pw_conf
		if [ "$root_pw" = "$root_pw_conf" ]; then
			pass_ok=1
		else
			echo
			echo "Password does not match."
			echo
		fi
	done
	echo "root:${root_pw}" | chpasswd
	echo
	echo
}


function set_timezone() {
	echo "-----------------------"
	echo "| Locale and Timezone |"
	echo "-----------------------"
	echo
	
	# Set locale, symlink to local time
	echo SETTING LOCALE
	echo 'en_US.UTF-8 UTF-8' >>/etc/locale.gen # How presumptuous of me. It's the 4th of July every day YEAAAAAAHHHHH!!!11!
	locale-gen
	clear

	# Get zoneinfo from user
	VALID_REGION=0
	regionArray=$(ls /usr/share/zoneinfo)
	while [ $VALID_REGION -eq 0 ]; do
		ls /usr/share/zoneinfo/
		echo 
		echo -n 'ENTER NAME OF REGION, EXACTLY AS IT APPEARS ABOVE: '
		read MYREGION	
		for region in ${regionArray[@]}; do
			if [ "$region" = $MYREGION ]; then
				VALID_REGION=1
			fi
		done
	done
	echo
	
	if [ -d /usr/share/zoneinfo/$MYREGION ]; then
		VALID_CITY=0
		cityArray=$(ls /usr/share/zoneinfo/$MYREGION)
		while [ $VALID_CITY -eq 0 ]; do
			ls /usr/share/zoneinfo/$MYREGION/
			echo $'\n\n\n'
			echo -n 'ENTER NAME OF CITY, EXACTLY AS IT APPEARS ABOVE: '
			read MYCITY
			for city in ${cityArray[@]}; do
				if [ "$city" = $MYCITY ]; then
					VALID_CITY=1;
				fi
			done
		done
	fi

	# Symlink time zone, sync hardware clock
	ln -sf /usr/share/zoneinfo/$MYREGION/$MYCITY /etc/localtime
	hwclock --systohc --utc

	echo
	echo
}

# Create user, password, change hostname
function create_user() {
	echo "-----------------"
	echo "| User Creation |"
	echo "-----------------"
	echo
	echo -n "Enter desired username: "
	read user_name
	echo
	useradd -m -G wheel -s /bin/bash $user_name
	echo $'\n'

	pass_ok=0
	while [ $pass_ok -eq 0 ]; do
		echo
		echo -n "Set password for $user_name: "
		read user_pw
		echo -n "Confirm password for $user_name: "
		read user_pw_conf
		if [ "$user_pw" = "$user_pw_conf" ]; then
			pass_ok=1
		else
			echo
			echo "Password does not match."
			echo
		fi
	done

	echo "${user_name}:${user_pw}" | chpasswd
	echo
	echo

	echo
	echo -n "Enter desired hostname: "
	read host_name
	echo $host_name > /etc/hostname
	echo
	echo
	
	# Add user to wheel
	echo "" >> /etc/sudoers
	echo "## Allow members of group wheel to execute any command" >> /etc/sudoers
	echo "%wheel ALL=(ALL) ALL" >> /etc/sudoers
	echo "## Enable password feedback" >> /etc/sudoers
	echo "Defaults env_reset,pwfeedback" >> /etc/sudoers

}


function install_packages() {
	echo "------------------------"
	echo "| Package Installation |"
	echo "------------------------"
	echo

	## Install yay
	#yaydir="/home/$user_name/yay"
	#echo "INSTALLING YAY"
	#echo
	#pacman -S -y --quiet --noconfirm git
	#su "$user_name" -c "git clone https://aur.archlinux.org/yay.git $yaydir"
	#chown -R $user_name $yaydir
	#cd "$yaydir"
	#su "$user_name" -c "makepkg -si"
	#wait
	#cd
	#rm -rf "$yaydir"

	# Install packages
	pacman -S -y --quiet --noconfirm bspwm sxhkd grub pulseaudio pulseaudio-alsa pavucontrol networkmanager network-manager-applet xf86-input-libinput mesa xorg xorg-xinit xorg-xbacklight redshift feh htop vim firefox base-devel bash-completion git acpi zathura zathura-djvu zathura-pdf-mupdf wget dmenu netctl dialog dhcpcd

	# Check video drivers
	echo "Checking graphics card..."
	ati=$(lspci | grep VGA | grep ATI)
	nvidia=$(lspci | grep VGA | grep NVIDIA)
	intel=$(lspci | grep VGA | grep Intel)
	amd=$(lspci | grep VGA | grep AMD)
	
	if [ ! -z "$ati" ]; then
	    echo 'Ati graphics detected'
	    pacman -S -y --quiet --noconfirm xf86-video-ati
	fi
	if [ ! -z "$nvidia" ]; then
	    echo 'Nvidia graphics detected'
	    pacman -S -y --quiet --noconfirm xf86-video-nouveau
	fi
	if [ ! -z  "$intel" ]; then
	    echo 'Intel graphics detected'
	    pacman -S -y --quiet --noconfirm xf86-video-intel
	fi
	if [ ! -z  "$amd" ]; then
	    echo 'AMD graphics detected'
	    pacman -S -y --quiet --noconfirm xf86-video-amdgpu
	fi
	echo
	echo
}


# Install grub
function install_grub() {
	clear
	echo "---------------------"
	echo "| Grub Installation |"
	echo "---------------------"

	echo 
	lsblk -l | grep disk
	echo 
	echo -n 'Enter disk to install grub to (NOT PARTITION): '
	read grub_disk
	grub-install --target=i386-pc /dev/$grub_disk
	grub-mkconfig -o /boot/grub/grub.cfg
	echo
}

function clean_up() {
	# Remove install scripts from root
	# (Exits chroot.sh - back into install.sh - and reboots from that script)
	rm /chroot.sh
}

set_root_pw
set_timezone
create_user
install_packages
install_grub
clean_up
