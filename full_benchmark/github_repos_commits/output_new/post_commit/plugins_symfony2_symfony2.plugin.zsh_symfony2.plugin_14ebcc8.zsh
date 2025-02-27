# Symfony2 basic command completion

_symfony2_get_command_list () {
################################################################################
# Commit message: #2893 generalized symfony2 console directory
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/14ebcc83bec267859e2948f36f48cc69f5150def
# Category: 
# Notes: 
# Changed content:
# - 	php app/console --no-ansi | sed "1,/Available commands/d" | awk '/^  [a-z]+/ { print $1 }'
# + 	php $(find . -maxdepth 2 -mindepth 1 -name 'console')  --no-ansi | sed "1,/Available commands/d" | awk '/^  [a-z]+/ { print $1 }'
################################################################################
# put stream annotation here
# stream enable
	php $(find . -maxdepth 2 -mindepth 1 -name 'console')  --no-ansi | sed "1,/Available commands/d" | awk '/^  [a-z]+/ { print $1 }'
}

_symfony2 () {
  if [ -f $(find . -maxdepth 2 -mindepth 1 -name 'console')  ]; then
    compadd `_symfony2_get_command_list`
  fi
}

compdef _symfony2 $(find . -maxdepth 2 -mindepth 1 -name 'console')
compdef _symfony2 sf

#Alias
alias sf='php $(find . -maxdepth 2 -mindepth 1 -name 'console') '
alias sfcl='php $(find . -maxdepth 2 -mindepth 1 -name 'console')  cache:clear'
alias sfroute='php $(find . -maxdepth 2 -mindepth 1 -name 'console')  router:debug'
alias sfcontainer='php $(find . -maxdepth 2 -mindepth 1 -name 'console') container:debug'
alias sfgb='php $(find . -maxdepth 2 -mindepth 1 -name 'console')  generate:bundle'
