# ------------------------------------------------------------------------------
#          FILE:  composer.plugin.zsh
#   DESCRIPTION:  oh-my-zsh composer plugin file.
#        AUTHOR:  Daniel Gomes (me@danielcsgomes.com)
#       VERSION:  1.0.0
# ------------------------------------------------------------------------------

# Composer basic command completion
_composer_get_command_list () {
################################################################################
# Commit message: Fix: "\s" is a gawk-specific regexp operator.
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/8b5950b812b56a652ce1101f8d4adc569e516160
# Category: 
# Notes: 
# Changed content:
# -     $_comp_command1 --no-ansi | sed "1,/Available commands/d" | awk '/^\s*[a-z]+/ { print $1 }'
# +     $_comp_command1 --no-ansi | sed "1,/Available commands/d" | awk '/^[ \t]*[a-z]+/ { print $1 }'
################################################################################
# put stream annotation here
# stream enable
    $_comp_command1 --no-ansi | sed "1,/Available commands/d" | awk '/^\s*[a-z]+/ { print $1 }'
}

_composer_get_required_list () {
    $_comp_command1 show -s --no-ansi | sed '1,/requires/d' | awk 'NF > 0 && !/^requires \(dev\)/{ print $1 }'
}

_composer () {
  local curcontext="$curcontext" state line
  typeset -A opt_args
  _arguments \
    '1: :->command'\
    '*: :->args'

  case $state in
    command)
      compadd $(_composer_get_command_list)
      ;;
    *)
      compadd $(_composer_get_required_list)
      ;;
  esac
}

compdef _composer composer
compdef _composer composer.phar

# Aliases
alias c='composer'
alias csu='composer self-update'
alias cu='composer update'
alias cr='composer require'
alias ci='composer install'
alias ccp='composer create-project'
alias cdu='composer dump-autoload'
alias cgu='composer global update'
alias cgr='composer global require'

# install composer in the current directory
alias cget='curl -s https://getcomposer.org/installer | php'

# Add Composer's global binaries to PATH
export PATH=$PATH:~/.composer/vendor/bin