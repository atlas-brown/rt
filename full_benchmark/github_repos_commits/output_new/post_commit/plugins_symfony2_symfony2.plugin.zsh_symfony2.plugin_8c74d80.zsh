# Symfony2 basic command completion

_symfony2_get_command_list () {
################################################################################
# Commit message: Fix Symfony2 command completion 'permission denied'  app/console by default (if you create a new Symfony project via composer create-project or by downloading it from symfony.com) is not executable. Therefore I get the following error:  sf2 _symfony2_get_command_list:1: permission denied: app/console  _symfony2_get_command_list:1: permission denied: app/console _symfony2_get_command_list:1: permission denied: app/console  To make command completion work without changing app/console you just have to let php run it.
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/8c74d80fd6cdc7e1b48e7eb321a3e3a22674c3be
# Category: 
# Notes: 
# Changed content:
# - 	app/console --no-ansi | sed "1,/Available commands/d" | awk '/^  [a-z]+/ { print $1 }'
# + 	php app/console --no-ansi | sed "1,/Available commands/d" | awk '/^  [a-z]+/ { print $1 }'
################################################################################
# put stream annotation here
# stream enable
	php app/console --no-ansi | sed "1,/Available commands/d" | awk '/^  [a-z]+/ { print $1 }'
}

_symfony2 () {
  if [ -f app/console ]; then
    compadd `_symfony2_get_command_list`
  fi
}

compdef _symfony2 app/console
compdef _symfony2 sf

#Alias
alias sf2='php app/console'
alias sf2clear='php app/console cache:clear'
