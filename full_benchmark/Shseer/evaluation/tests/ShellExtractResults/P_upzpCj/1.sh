#!/bin/bash

cp -rfv manual/ /var/www/pstar/
cp -fv .htaccess * /var/www/pstar/
chown -R www-data /var/www/pstar/*

