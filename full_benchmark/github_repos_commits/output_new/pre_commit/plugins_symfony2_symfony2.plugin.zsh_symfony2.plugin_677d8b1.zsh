# Symfony2 basic command completion

_symfony_console () {
################################################################################
# Commit message: Symfony2 plugin look for files only
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/677d8b1a21c4b1d8cffef4cbfa259797a11f338a
# Category: 
# Notes: 
# Changed content:
# -   echo "php $(find . -maxdepth 2 -mindepth 1 -name 'console' | head -n 1)"
# +   echo "php $(find . -maxdepth 2 -mindepth 1 -name 'console' -type f | head -n 1)"
################################################################################
# put stream annotation here
# stream enable
  echo "php $(find . -maxdepth 2 -mindepth 1 -name 'console' | head -n 1)"
}

_symfony2_get_command_list () {
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