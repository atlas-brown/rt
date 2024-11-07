#!/bin/bash

## Core utils
apt-get install -y vim tar nano net-tools telnet curl wget telnet

## Classic tools
apt-get install -y lynx

## Workflow tools
apt-get install -y tree

## Image utils
apt-get install -y ImageMagick

## Forensics and penetration tools
apt-get install -y hydra john nmap aircrack-ng

# sqlmap
git clone https://github.com/sqlmapproject/sqlmap.git /opt/sqlmap

## Privacy tools
apt-get install -y tor gnupg

## proxychains
apt-get install -y proxychains
(
  sed -Ei 's/strict_chain/random_chain/g' /etc/proxychains.conf
  echo "socks4  58.20.0.246 1080" >> /etc/proxychains.conf
  echo "socks5  109.251.162.7 1080" >> /etc/proxychains.conf
  echo "socks4  125.71.88.121 1080" >> /etc/proxychains.conf
  echo "socks4  14.156.144.115 1080" >> /etc/proxychains.conf
  echo "socks4  181.15.217.116 1080" >> /etc/proxychains.conf
)

# torsocks-2.0.0
(
  rm `which torsocks`
  cd /tmp
  wget -O torsocks-2.0.0.tar.gz https://github.com/dgoulet/torsocks/archive/v2.0.0.tar.gz
  tar -xzf torsocks-2.0.0.tar.gz
  (
    cd torsocks-2.0.0
    ./autogen.sh && ./configure && make && make install
  )
)

