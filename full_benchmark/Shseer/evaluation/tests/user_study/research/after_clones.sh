#!/bin/bash
# vim: fdm=expr fdc=1 ft=shbuild:

# Joseph Harriott
# grab repositories
# bash clones.sh

cdp="cd $HOME/.vim/pack"

#=> 1 packs
gc='git clone'
gd(){ echo $1; [[ -d $1 ]] || mkdir $1; cd $1; }

#==> ft
echo; $cdp; gd ft

gd start; ls
  # $gc https://github.com/christianrondeau/vim-base64
  # $gc https://github.com/jtratner/vim-flavored-markdown
  # $gc https://github.com/PProvost/vim-ps1
  # $gc https://github.com/vim-pandoc/vim-pandoc-syntax
  # $gc https://github.com/vim-scripts/python_match.vim
cd ..

#==> git
echo; $cdp; gd git

gd start; ls
  # $gc https://github.com/tpope/vim-fugitive
  # $gc https://github.com/tpope/vim-rhubarb
cd ..

#==> layout
echo; $cdp; gd layout

gd opt; ls

  # $gc https://github.com/chrisbra/Colorizer
  # $gc https://github.com/inkarkat/vim-ShowTrailingWhitespace
  # $gc https://github.com/junegunn/limelight.vim
  # $gc https://github.com/lilydjwg/colorizer
  # $gc https://github.com/ntpeters/vim-better-whitespace

cd ..

gd start; ls

  # $gc https://github.com/chunkhang/vim-mbsync
  # $gc https://github.com/drmikehenry/vim-fontsize
  # $gc https://github.com/junegunn/vim-easy-align
  # $gc https://github.com/mhinz/vim-startify
  # $gc https://github.com/svermeulen/vim-colors-tomorrow
  # $gc https://github.com/vim-scripts/gitignore.vim

cd ..

#==> neovim
echo; $cdp; gd neovim

gd opt; ls
  # $gc https://github.com/RRethy/vim-hexokinase; cd vim-hexokinase; make hexokinase; cd ..
cd ..

#==> other
echo; $cdp; gd other

gd start; ls

  # $gc https://github.com/AndrewRadev/bufferize.vim
  # $gc https://github.com/Asheq/close-buffers.vim
  # $gc https://github.com/bronson/vim-visual-star-search
  # $gc https://github.com/haya14busa/incsearch-fuzzy.vim
  # $gc https://github.com/haya14busa/incsearch.vim
  # $gc https://github.com/unblevable/quick-scope
  # $gc https://github.com/wellle/targets.vim
  # $gc https://github.com/tpope/vim-repeat

cd ..

#==> shell
echo; $cdp; gd shell

gd start; ls

  # $gc https://github.com/dhruvasagar/vim-open-url
  # $gc https://github.com/harriott/vim-buffing-wheel
  # $gc https://github.com/junegunn/fzf.vim
  # $gc https://github.com/scrooloose/nerdtree
  # $gc https://github.com/srstevenson/vim-picker
  # $gc https://github.com/tyru/open-browser.vim
  # $gc https://github.com/yegappan/mru

cd ..

#=> 2 lists
echo; $cdp
. ArchLinux/lists.sh

