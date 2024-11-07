#!/usr/bin/env bash

set -e

log () {
  echo -e "\n=> $1\n"
}

log "Update aptitude"
apt-get update
apt-get install curl python-software-properties --yes

log "Installing postgresql"
echo "deb http://apt.postgresql.org/pub/repos/apt/ lucid-pgdg main" > /etc/apt/sources.list.d/pgdg.list
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
apt-get update
apt-get install postgresql-contrib-9.3 --yes

log "Setting up wivern"
cd /vagrant
su vagrant -lc "cd /vagrant && bundle install"
cp .env.example .env

log "Setting up the database"
cp config/database.yml.example config/database.yml &&
su vagrant -lc "cd /vagrant && bin/rake db:setup"

log "Install upstart script"
su vagrant -lc "cd /vagrant && sudo foreman export upstart /etc/init \
  --app wivern \
  --user vagrant \
  --log /vagrant/log \
  --template /vagrant/config/vagrant/foreman/export_templates/upstart"

log "Starting wivern"
start wivern

cat <<"EOF"
-------------------------------------------------------------------------------
       ___       __   ___  ___      ___ _______   ________  ________           
      |\  \     |\  \|\  \|\  \    /  /|\  ___ \ |\   __  \|\   ___  \         
      \ \  \    \ \  \ \  \ \  \  /  / | \   __/|\ \  \|\  \ \  \\ \  \        
       \ \  \  __\ \  \ \  \ \  \/  / / \ \  \_|/_\ \   _  _\ \  \\ \  \       
        \ \  \|\__\_\  \ \  \ \    / /   \ \  \_|\ \ \  \\  \\ \  \\ \  \      
         \ \____________\ \__\ \__/ /     \ \_______\ \__\\ _\\ \__\\ \__\     
          \|____________|\|__|\|__|/       \|_______|\|__|\|__|\|__| \|__|     



                         __ ___                                                
                        /__/ _ \                                               
                        |__|(_)|  An Assembly Product                          
                        \__\___/                                               




Open up http://localhost:5000 in your browser to get started.

-------------------------------------------------------------------------------
EOF

set +e
