# Symfony2 basic command completion

_symfony_console () {
  echo "php $(find . -maxdepth 2 -mindepth 1 -name 'console')"
}

_symfony2_get_command_list () {
################################################################################
# Commit message: #2914 fixed symfony2 autocomplete
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/bb928b59c409feacc660a64e800ce9129c058104
# Category: 
# Notes: 
# Changed content:
# - php $(find . -maxdepth 2 -mindepth 1 -name 'console')  --no-ansi | sed "1,/Available commands/d" | awk '/^  [a-z]+/ { print $1 }'
# + `_symfony_console` --no-ansi | sed "1,/Available commands/d" | awk '/^  [a-z]+/ { print $1 }'
################################################################################
# put stream annotation here
# stream enable
   `_symfony_console` --no-ansi | sed "1,/Available commands/d" | awk '/^  [a-z]+/ { print $1 }'
}

_symfony2 () {
   compadd `_symfony2_get_command_list`
}

compdef _symfony2 '`_symfony_console`'
compdef _symfony2 sf

#Alias
alias sf='`_symfony_console`'
alias sfcl='sf cache:clear'
alias sfcw='sf cache:warmup'
alias sfroute='sf router:debug'
alias sfcontainer='sf container:debug'
alias sfgb='sf generate:bundle'