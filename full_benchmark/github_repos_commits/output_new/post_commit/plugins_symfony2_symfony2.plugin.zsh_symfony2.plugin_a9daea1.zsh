# Symfony2 basic command completion

_symfony_console () {
  echo "php $(find . -maxdepth 2 -mindepth 1 -name 'console' -type f | head -n 1)"
}

_symfony2_get_command_list () {
################################################################################
# Commit message: plugin symfony2 sf2.7 compatibility fix  with symfony 2.7 command group titles are listed as commands. this commit prevents it.
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/a9daea17d89ae2b7d30dc6e184566ca8104e63d2
# Category: 
# Notes: 
# Changed content:
# - `_symfony_console` --no-ansi | sed "1,/Available commands/d" | awk '/^  ?[a-z]+/ { print $1 }'
# + `_symfony_console` --no-ansi | sed "1,/Available commands/d" | awk '/^  ?[^ ]+ / { print $1 }'
################################################################################
# put stream annotation here
# stream enable
   `_symfony_console` --no-ansi | sed "1,/Available commands/d" | awk '/^  ?[^ ]+ / { print $1 }'
}

_symfony2 () {
   compadd `_symfony2_get_command_list`
}

compdef _symfony2 '`_symfony_console`'
compdef _symfony2 'app/console'
compdef _symfony2 'bin/console'
compdef _symfony2 sf

#Alias
alias sf='`_symfony_console`'
alias sfcl='sf cache:clear'
alias sfsr='sf server:run -vvv'
alias sfcw='sf cache:warmup'
alias sfroute='sf router:debug'
alias sfcontainer='sf container:debug'
alias sfgb='sf generate:bundle'