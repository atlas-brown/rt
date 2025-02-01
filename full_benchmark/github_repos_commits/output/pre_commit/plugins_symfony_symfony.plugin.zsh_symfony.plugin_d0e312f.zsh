# symfony basic command completion

_symfony_get_command_list () {
################################################################################
# Commit message: Fix symfony command completion 'permission denied'
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/d0e312fc13d8f2a1a6bb9a02ca4acf1bcdc0bbfe
# Category: hard awk
# Notes: 
# Changed content:
# -     ./symfony | sed "1,/Available tasks/d" | awk 'BEGIN { cat=null; } /^[A-Za-z]+$/ { cat = $1; } /^  :[a-z]+/ { print cat $1; }'
# +     php symfony | sed "1,/Available tasks/d" | awk 'BEGIN { cat=null; } /^[A-Za-z]+$/ { cat = $1; } /^  :[a-z]+/ { print cat $1; }'
################################################################################
# put stream annotation here
# stream enable
    ./symfony | sed "1,/Available tasks/d" | awk 'BEGIN { cat=null; } /^[A-Za-z]+$/ { cat = $1; } /^  :[a-z]+/ { print cat $1; }'
}

_symfony () {
  if [ -f symfony ]; then
    compadd `_symfony_get_command_list`
  fi
}

compdef _symfony symfony