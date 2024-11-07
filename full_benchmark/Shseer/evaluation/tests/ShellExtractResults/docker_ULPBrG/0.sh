#!/bin/sh

# Switch to app dir
cd /home/app/frab

# Create shared public folder if it doesn't exist
if [ ! -d /home/app/shared/public/ ]; then
	mkdir -p /home/app/shared/public/
	chown -R app:app /home/app/shared/public/
fi

# Symlink system folder
if [ ! -h public/system ]; then
	ln -s /home/app/shared/public/ public/system
fi

# Remove old symlinks
if [ -h /home/app/frab/config/initializers/secret_token.rb ]; then
	rm /home/app/frab/config/initializers/secret_token.rb
fi

if [ -h /home/app/frab/config/database.yml ]; then
	rm /home/app/frab/config/database.yml
fi

if [ -h /home/app/frab/config/settings.yml ]; then
        rm /home/app/frab/config/settings.yml
fi

# Symlink .env
if [ ! -f /home/app/frab/.env ]; then
	ln -s /home/app/shared/.env /home/app/frab/.env
fi

# Precompile assets
sudo -u app RAILS_ENV=production bundle exec rake assets:precompile

# Setup database if frab is not installed
if [ ! -f /home/app/shared/installed ]; then
	sudo -u app RAILS_ENV=production bundle exec rake db:setup
	touch /home/app/shared/installed
fi

# Migrate database on startup
sudo -u app RAILS_ENV=production bundle exec rake db:migrate
