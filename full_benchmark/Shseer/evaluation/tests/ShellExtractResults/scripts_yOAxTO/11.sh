#!/bin/bash

brew install qt

cd ${HOME}
git clone https://github.com/equalsraf/neovim-qt.git && \
    cd neovim-qt && \
    mkdir build && cd build && \
    cmake -DCMAKE_BUILD_TYPE=Release .. && \
    make -j $(nproc) && \
    make install && \
    cd ${HOME} && \
    rm -r neovim-qt


python3 -m pip install --user --upgrade pynvim
