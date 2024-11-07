#!/bin/sh

set -eo pipefail

#apt-get update && apt-get -y install \
#    neovim-qt
#
#printf "Finished nvim gui setup\n"

cd ${HOME}
# Replace with original once merged!
git clone https://github.com/f-squirrel/neovim-qt.git --depth 1 --branch implement_frameless

if [[ -n $LOCAL_INSTALLATION ]]; then
    cd neovim-qt
    mkdir build
    cmake -DCMAKE_BUILD_TYPE=Release ..
    make -j $(nproc)
    make install
    rm -r neovim-qt
fi
