#!/bin/bash

# root setup script is installing byobu, parted, git and zsh

# Add users, and copy public keys
BASEDIR=$(dirname "$0")
for user in $(ls $BASEDIR/keys); do
  useradd -m $user
  usermod -aG sudo $user 
  chsh -s /bin/bash $user
  cp -R $BASEDIR/keys/$user/. /home/$user/
  chown -R $user:$user /home/$user
done
sed -i "s/^%sudo/# %sudo/" /etc/sudoers
echo "%sudo ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
touch /var/lib/cloud/instance/warnings/.skip

# Initialize disks
uninit_dsks=$(lsblk -r --output NAME,MOUNTPOINT | awk -F \/ '/sd/ { dsk=substr($1,1,3);dsks[dsk]+=1 } END { for ( i in dsks ) { if (dsks[i]==1) print i } }')
dsks=()
for dsk in $uninit_dsks; do
  parted /dev/$dsk --script -- mklabel gpt mkpart primary 0% 100%;
  dsks+=("/dev/${dsk}1")
done;

NVME_DEV="/dev/nvme0n1"
if [ -e "$NVME_DEV" ]; then
  dsks+=("$NVME_DEV")
fi

sleep 5
echo y | mdadm --create --verbose --level=0 --metadata=1.2 --raid-devices=${#dsks[@]} /dev/md/build "${dsks[@]}"
echo 'DEVICE partitions' > /etc/mdadm.conf
mdadm --detail --scan >> /etc/mdadm.conf
mdadm --assemble --scan
mkfs.ext4 /dev/md/build
mkdir -p /raid
mount /dev/md/build /raid

# Populate fstab
RAID_UUID=$(blkid -s UUID -o value /dev/md/build)
echo -e "UUID=${RAID_UUID}\t/raid\text4\trw,relatime,defaults\t0\t1" >> /etc/fstab

# h5ai setup
DEBIAN_FRONTEND=noninteractive apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install unzip nginx php7.2-fpm php7.2-mysql php7.2-mbstring php7.2-curl php7.2-dom -y
mkdir -p /raid/h5ai
wget https://release.larsjung.de/h5ai/h5ai-0.29.2.zip -O /raid/h5ai.zip
unzip /raid/h5ai.zip -d /raid/h5ai/
cp $BASEDIR/h5ai_nginx /etc/nginx/sites-available/h5ai
sed -i "s/HOSTNAME/$(echo $HOSTNAME | tr '[:upper:]' '[:lower:]')/g" /etc/nginx/sites-available/h5ai
ln -s /etc/nginx/sites-available/h5ai /etc/nginx/sites-enabled/h5ai
systemctl start nginx

# hand over dem perms
chown -R jenkins:jenkins /raid

# Android build env setup
git config --global user.email "botatosalad@deletescape.ch"
git config --global user.name "Botato Salad"
git clone https://github.com/AgentFabulous/scripts ~/.android-scripts
cd ~/.android-scripts
bash setup/android_build_env.sh
cd -

# Update CloudFlare DNS records

api_token="$1"
record_alias="$2"
zone_name="$3"

$BASEDIR/cloudflare-update.sh $api_token $record_alias $zone_name "false"
$BASEDIR/cloudflare-update.sh $api_token "${record_alias}-mirror" $zone_name "true"

# Cleanup
rm -rf ~/.android-scripts
rm -rf ~/.setup-scripts
