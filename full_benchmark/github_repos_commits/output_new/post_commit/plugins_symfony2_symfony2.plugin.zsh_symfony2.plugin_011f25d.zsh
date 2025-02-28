# Symfony2 basic command completion

_symfony_console () {
  echo "php $(find . -maxdepth 2 -mindepth 1 -name 'console' -type f | head -n 1)"
}

_symfony2_get_command_list () {
################################################################################
# Commit message: Fixed command autocomplete for Symfony 2.6.x
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/011f25d492ab23b0f1dd50ea0f406892810e781e
# Category: 
# Notes: 
# Changed content:
# - `_symfony_console` --no-ansi | sed "1,/Available commands/d" | awk '/^  [a-z]+/ { print $1 }'
# + `_symfony_console` --no-ansi | sed "1,/Available commands/d" | awk '/^  ?[a-z]+/ { print $1 }'
################################################################################
# put stream annotation here
# stream enable
   `_symfony_console` --no-ansi | sed "1,/Available commands/d" | awk '/^  ?[a-z]+/ { print $1 }'
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
alias sfcw='sf cache:warmup'
alias sfroute='sf router:debug'
alias sfcontainer='sf container:debug'
alias sfgb='sf generate:bundle'