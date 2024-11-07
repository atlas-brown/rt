#!/bin/sh

mkdir -p parts_tmp
rm parts_tmp/* 

./generate_web_docs.sh

mkdir -p /var/www/pstar/docs
cp -f parts_tmp/ch03* /var/www/pstar/docs
cp -f ch3_index.pstar /var/www/pstar/docs

cp -rf parts_tmp/images /var/www/pstar/
