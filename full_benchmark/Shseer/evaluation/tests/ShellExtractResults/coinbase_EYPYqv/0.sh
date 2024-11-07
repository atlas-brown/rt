#!/usr/bin/env bash

# Set up the virtual env.
virtualenv venv --distribute
source venv/bin/activate
pip install -r requirements.txt

read -p "Is this for an existing Heroku app? [y/N] " -r
if [[ $REPLY =~ ^[Yy]$ ]]
then
  # Add existing app as remote.
  read -p 'Enter existing app name: ' app_name
  heroku git:remote -a $app_name
else
  # Create a new heroku app.
  read -p 'Enter new app name (will be used for <name>.herokuapp.com): ' app_name
  heroku create $app_name
fi


# Set up the keys for the API/Flask.
read -p 'Enter API client id: ' client_id
heroku config:set "API_CLIENT_ID=$client_id"

read -p 'Enter API client secret: ' client_secret
heroku config:set "API_CLIENT_SECRET=$client_secret"

heroku config:set "FLASK_SECRET=`cat /dev/urandom | head -c 1 | md5sum - | awk '{print $1}'`"

# Put config in .env so foreman can use it.
heroku config | tail -n+2 > .env

# Push and open the app.
git push heroku master
heroku ps:scale web=1
heroku open

echo '
 _____     ____    _   _   ______
 |  __ \   / __ \  | \ | | |  ____|
 | |  | | | |  | | |  \| | | |__
 | |  | | | |  | | | . ` | |  __|
 | |__| | | |__| | | |\  | | |____
 |_____/   \____/  |_| \_| |______|
'

echo 'Now run "source venv/bin/activate" and have fun!'
