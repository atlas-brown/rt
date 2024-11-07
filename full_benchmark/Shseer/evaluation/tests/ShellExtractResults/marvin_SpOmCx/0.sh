#!/usr/bin/env bash

apt-get update
apt-get install -y g++ make vim git redis-server build-essential libffi-dev
apt-get install -y python-software-properties python python-pip python-dev python-lxml

#marvin configuration.  see readme.md
cd /vagrant
pip install -r requirements.txt
cp core/config.copy config
