#!/bin/sh
# (C) 2015 Gunnar Andersson
# This file is part of franca_install_automation
# License: See project directory
branch=$(git status -b -s | grep '##' | cut -c 4-)
ver=mars-SR2
arch=x86_64
variant=linux-gtk
francaver=0.9.1

tag=franca_$francaver-$ver-$variant-$arch-$branch

git tag -f $tag

