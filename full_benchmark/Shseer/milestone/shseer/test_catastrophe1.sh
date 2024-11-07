#!/bin/sh
link="https://dummy.com/download"
install_dir="$HOME"$2
mkdir -p "$install_dir"
cd "$install_dir" || exit 1
rm -fr ./*
wget -O z3zip $link
unzip z3zip 


