#!/bin/bash

gvim_helper() {
    NVIM_QT_RUNTIME_PATH=/usr/local/share/nvim-qt/runtime ${NVIM_QT_PATH} "$@"
}

alias gvim='gvim_helper "$@"'
alias gview='gvim "$@" -- -R'
alias gvimdiff='${NVIM_QT_PATH} "$@" -- -d'
