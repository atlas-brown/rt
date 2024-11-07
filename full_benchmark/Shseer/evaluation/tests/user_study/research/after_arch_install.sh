#!/bin/bash

Bold=$(tput bold)
Reset=$(tput sgr0)
MOUNTPOINT="/mnt"

print_title() {
    #clear
    echo ""
    echo "******************************"
    echo -e "# ${Bold}$1${Reset}"
    echo "******************************"
}

pause_function() {
    read -e -sn 1 -p "Press a key to continue..."
}

arch_chroot() {
    arch-chroot $MOUNTPOINT /bin/bash -c "${1}"
}

print_title "Update the system clock"
timedatectl set-ntp true
pause_function

print_title "Test internet connection"
# Test internet connection
ping -c 3 www.google.com
pause_function

print_title "Update mirror list"
curl -O https://raw.githubusercontent.com/Gen2ly/armrr/master/armrr
chmod +x armrr 
./armrr US
pause_function

print_title "Install arch-install-scripts"
pacman -Syy
wget https://git.archlinux.org/arch-install-scripts.git/snapshot/arch-install-scripts-23.tar.gz
tar zxvf arch-install-scripts-23.tar.gz
cd arch-install-scripts-23
pause_function

print_title "Load partitions"
lsblk
read -p "Enter the swap partition: " SWAP
read -p "Enter the root partition: " ROOT

print_title "Setup and activate Swap"
# Swap set up and activated
mkswap /dev/$SWAP
swapon /dev/$SWAP
pause_function

print_title "Mount the root partition"
# Mount the root partition
mount /dev/$ROOT /mnt
pause_function

print_title "Install the base system"
# Install the base system
pacstrap -i /mnt base base-devel linux linux-firmware
pause_function

print_title "Generate fstab"
# Generate an fstab
genfstab -U -p /mnt >> /mnt/etc/fstab
echo "--fstab--"
# View fstab
cat /mnt/etc/fstab
pause_function

print_title "Setup locale"
# Uncomment en_US.UTF-8 UTF-8 locale
arch_chroot "sed -i 's/#en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen"
# arch_chroot "nano /etc/locale.gen"
# Generate locale
arch_chroot "locale-gen"
pause_function

print_title "Set timezone"
# Set timezone
arch_chroot "ln -sf /usr/share/zoneinfo/US/Mountain /etc/localtime"
pause_function

print_title "Set hardware clock to UTC"
# set the hardware clock to UTC
arch_chroot "hwclock --systohc --utc"
pause_function

print_title "Set hostname"
# Set the hostname
arch_chroot "echo Yavin > /etc/hostname"
# Add the same hostname to /etc/hosts
# arch_chroot "nano /etc/hosts"
arch_chroot "sed -i '/^127./ s/$/ Yavin/' /etc/hosts"
arch_chroot "sed -i '/^::1/ s/$/ Yavin/' /etc/hosts"
pause_function

print_title "Network interface"
# View network interface
arch_chroot "pacman -S dhcpcd"
arch_chroot "ip link"
read -p "Enter interface name: " IFACE
echo "Enable DHCP"
# Enable DHCP
arch_chroot "systemctl enable dhcpcd@$IFACE.service"
pause_function

print_title "Set root password"
# Set the root password
arch_chroot "passwd"
pause_function

print_title "Install grub and wget"
# Install the grub package
arch_chroot "pacman -S grub os-prober wget efibootmgr nano"

print_title "Install bootloader"
# Install the bootloader
arch_chroot "mkdir /boot/EFI"
arch_chroot "mount /dev/sda2 /boot/EFI"
arch_chroot "grub-install --target=x86_64-efi --efi-directory=/boot/EFI --bootloader-id=Arch --recheck"

print_title "Generate grub.cfg"
# Generate grub.cfg
arch_chroot "grub-mkconfig -o /boot/grub/grub.cfg"
pause_function

print_title "Exit"
# Exit and unmount system
arch_chroot "exit"
umount -R /mnt
#reboot
