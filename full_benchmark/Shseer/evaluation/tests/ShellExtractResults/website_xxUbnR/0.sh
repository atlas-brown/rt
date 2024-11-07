#!/bin/bash

cd /var/www/laravel.com/sami

rm -rf /var/www/laravel.com/sami/build
rm -rf /var/www/laravel.com/sami/cache

# Run API Docs For Master
git clone https://github.com/laravel/framework.git /var/www/laravel.com/sami/laravel

php /var/www/laravel.com/sami/sami.php update /var/www/laravel.com/sami/config.php

cp -r /var/www/laravel.com/sami/build/* /var/www/laravel.com/public/api/master

rm -rf /var/www/laravel.com/sami/build
rm -rf /var/www/laravel.com/sami/cache

# Run API Docs For 4.1
cd /var/www/laravel.com/sami/laravel
git checkout -b 4.1 origin/4.1
cd ..

php /var/www/laravel.com/sami/sami.php update /var/www/laravel.com/sami/config.php

cp -r /var/www/laravel.com/sami/build/* /var/www/laravel.com/public/api/4.1

rm -rf /var/www/laravel.com/sami/build
rm -rf /var/www/laravel.com/sami/cache

# Run API Docs For 4.0
cd /var/www/laravel.com/sami/laravel
git checkout -b 4.0 origin/4.0
cd ..

php /var/www/laravel.com/sami/sami.php update /var/www/laravel.com/sami/config.php

cp -r /var/www/laravel.com/sami/build/* /var/www/laravel.com/public/api/4.0

rm -rf /var/www/laravel.com/sami/build
rm -rf /var/www/laravel.com/sami/cache

# Cleanup
rm -rf /var/www/laravel.com/sami/laravel