#!/bin/bash
set -e
apt-get update
apt-get -y install python-software-properties
apt-add-repository "deb http://archive.canonical.com/ $(lsb_release -sc) partner"
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get -y upgrade
apt-get -y install \
  vim x11vnc xvfb fluxbox skype dbus dbus-x11 \
  python-pip python-virtualenv python-dbus python-gobject
