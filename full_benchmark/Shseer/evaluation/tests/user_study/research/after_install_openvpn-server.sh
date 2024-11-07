#!/bin/bash

# OpenVPN Deiban 9 version

DEBIAN_FRONTEND=noninteractive
export DEBIAN_FRONTEND

set -e

arg1=$1
arg2=$2

echo " >>>> Installation de OpenVPN Server <<<<"

# Params
openvpn_root="/root/vpn"
openvpn_ca=${openvpn_root}/openvpn-ca
clients=${openvpn_root}/client-configs
install_files="/root/tmp/install"


# Check TERM
if [ -z ${TERM} ] ; then
    export TERM=vt100
else
    set +e
    isscreen=$(echo $TERM | grep "screen")
    if [ ! -z ${isscreen} ] ; then
        export TERM=vt100
    fi
    set -e
fi
#echo $TERM


# Prerequisites
apt update
apt -y upgrade
apt install -y openvpn easy-rsa wget hostname whiptail gzip


# Creation/effacement du repertoire
if [ -f ${openvpn_root} ] || [ -d ${openvpn_root} ] ; then
    if (whiptail --title "${openvpn_root} deja present" --yesno "Effacer ${openvpn_root} ?" 10 60) then
        rm -rf ${openvpn_root}
    fi
fi
mkdir -p ${openvpn_root}


# Copy OpenVPN templates in directory
mkdir -p ${clients}/
if [ -f "${install_files}/client.conf" ]; then
    cp ${install_files}/client.conf ${clients}/base.conf
else
    echo "Error! Client config file not present : ${install_files}/client.conf"
    exit 1
fi
if [ -f "${install_files}/make-client-config.sh" ]; then
    cp ${install_files}/make-client-config.sh ${openvpn_root}/make-client-config.sh
fi


# Create easy-rsa template dir
make-cadir ${openvpn_ca}
cd ${openvpn_ca}


# Config vars file
if [ -f "/root/vars" ] ; then
    # Test if own parameters are present
    source /root/vars
else
    # Or ask user
    KEY_COUNTRY=$(whiptail --title "Input" --inputbox "KEY_COUNTRY ?" 10 60 FR 3>&1 1>&2 2>&3)
    exitstatus=$? && if [ ! $exitstatus = 0 ]; then echo "Aborted!" && exit 1 ; fi

    KEY_PROVINCE=$(whiptail --title "Input" --inputbox "KEY_PROVINCE ?" 10 60 Paris 3>&1 1>&2 2>&3)
    exitstatus=$? && if [ ! $exitstatus = 0 ]; then echo "Aborted!" && exit 1 ; fi

    KEY_CITY=$(whiptail --title "Input" --inputbox "KEY_CITY ?" 10 60 Paris 3>&1 1>&2 2>&3)
    exitstatus=$? && if [ ! $exitstatus = 0 ]; then echo "Aborted!" && exit 1 ; fi

    KEY_ORG=$(whiptail --title "Input" --inputbox "KEY_ORG ?" 10 60 Nextdom 3>&1 1>&2 2>&3)
    exitstatus=$? && if [ ! $exitstatus = 0 ]; then echo "Aborted!" && exit 1 ; fi

    KEY_EMAIL=$(whiptail --title "Input" --inputbox "KEY_EMAIL ?" 10 60 admin@example.com 3>&1 1>&2 2>&3)
    exitstatus=$? && if [ ! $exitstatus = 0 ]; then echo "Aborted!" && exit 1 ; fi

    KEY_OU=$(whiptail --title "Input" --inputbox "KEY_OU ?" 10 60 Community 3>&1 1>&2 2>&3)
    exitstatus=$? && if [ ! $exitstatus = 0 ]; then echo "Aborted!" && exit 1 ; fi

fi

sed -i "s#^export KEY_COUNTRY=.*#export KEY_COUNTRY=\"$KEY_COUNTRY\"#g" ${openvpn_ca}/vars
sed -i "s#^export KEY_PROVINCE=.*#export KEY_PROVINCE=\"$KEY_PROVINCE\"#g" ${openvpn_ca}/vars
sed -i "s#^export KEY_CITY=.*#export KEY_CITY=\"$KEY_CITY\"#g" ${openvpn_ca}/vars
sed -i "s#^export KEY_ORG=.*#export KEY_ORG=\"$KEY_ORG\"#g" ${openvpn_ca}/vars
sed -i "s#^export KEY_EMAIL=.*#export KEY_EMAIL=\"$KEY_EMAIL\"#g" ${openvpn_ca}/vars
sed -i "s#^export KEY_OU=.*#export KEY_OU=\"$KEY_OU\"#g" ${openvpn_ca}/vars
sed -i "s#^export KEY_NAME=.*#export KEY_NAME=\"server\"#g" ${openvpn_ca}/vars


cd ${openvpn_ca}
if [ ! -f "openssl.cnf" ] ; then
    ln -s openssl-1.0.0.cnf openssl.cnf
fi

# Building the CA
cd ${openvpn_ca}
source vars

# Clean all
./clean-all

export EASY_RSA="${EASY_RSA:-.}"

# build root CA
#./build-ca
"$EASY_RSA/pkitool" --initca

# generating the OpenVPN server certificate and key pair
#./build-key-server server
"$EASY_RSA/pkitool" --server server

# generating a robust Diffie-Hellman key
./build-dh

# generating a HMAC signature
openvpn --genkey --secret keys/ta.key


# Configurate OpenVPN server
cd ${openvpn_ca}/keys
cp -ax ca.crt server.crt server.key ta.key dh2048.pem /etc/openvpn/


# Adjusting the Server Networking Configuration
sed -i 's/^#net.ipv4.ip_forward=1.*/net.ipv4.ip_forward=1/g' /etc/sysctl.conf
sysctl -p

# OpenVPN server config file
if [ -f "${install_files}/server.conf" ]; then
    cp ${install_files}/server.conf /etc/openvpn/server.conf
else
    gunzip -c /usr/share/doc/openvpn/examples/sample-config-files/server.conf.gz > /etc/openvpn/server.conf

    sed -i 's/^proto udp.*/;proto udp/g' /etc/openvpn/server.conf
    sed -i 's/^;proto tcp.*/proto tcp/g' /etc/openvpn/server.conf
    sed -i 's/^proto .*/proto tcp/g' /etc/openvpn/server.conf

    sed -i 's/^port .*/port 8443/g' /etc/openvpn/server.conf

    sed -i 's/^;tls-auth .*/tls-auth ta.key 0/g' /etc/openvpn/server.conf
    sed -i '/^tls-auth ta.key 0/a key-direction 0' /etc/openvpn/server.conf

    sed -i 's/^;cipher .*/cipher AES-256-CBC/g' /etc/openvpn/server.conf
    sed -i '/^cipher AES-256-CBC/a auth SHA256' /etc/openvpn/server.conf

    sed -i 's/^;user .*/user nobody/g' /etc/openvpn/server.conf
    sed -i 's/^;group .*/group nogroup/g' /etc/openvpn/server.conf

    sed -i 's/^explicit-exit-notify /;explicit-exit-notify /g' /etc/openvpn/server.conf
fi


# Adjusting UFW configuration
#apt install -y ufw
##
#sed -i "/^# Don't delete these required lines.*/i # START OPENVPN RULES\n# NAT table rules\n*nat\n:POSTROUTING ACCEPT [0:0] \n# Allow traffic from OpenVPN client to eth0 (change to the interface you discovered)\n-A POSTROUTING -s 10.8.0.0/8 -o eth0 -j MASQUERADE\nCOMMIT\n# END OPENVPN RULES\n" /etc/ufw/before.rules
#sed -i 's/^DEFAULT_FORWARD_POLICY="DROP"/DEFAULT_FORWARD_POLICY="ACCEPT"/g' /etc/default/ufw
#ufw allow 1194/udp
#ufw allow OpenSSH
#ufw disable
#ufw enable


# Virtual interface
mkdir -p /dev/net
set +e
mknod /dev/net/tun c 10 200
set -e


# Starting and Enabling the OpenVPN Service
systemctl start openvpn@server
systemctl enable openvpn@server

ip addr show tun0

# Show IP
ip=$(hostname -I)
echo " >>>>  OpenVPN IP: ${ip} <<<<"
