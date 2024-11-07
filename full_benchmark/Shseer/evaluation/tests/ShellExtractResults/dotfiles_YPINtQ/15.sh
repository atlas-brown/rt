#!/bin/sh

# Using Non-System Ruby
#
# brew install rbenv ruby-build
# rbenv install 2.1.5
# rbenv global 2.1.5
# ruby -v
export RBENV_ROOT="$(brew --prefix rbenv)"
export GEM_HOME="$(brew --prefix)/opt/gems"
export GEM_PATH="$(brew --prefix)/opt/gems"

if which rbenv > /dev/null;
  then eval "$(rbenv init -)";
fi

PATH=$GEM_PATH/bin:$PATH
export PATH
