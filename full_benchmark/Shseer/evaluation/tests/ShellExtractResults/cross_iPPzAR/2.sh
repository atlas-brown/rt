#!/bin/bash
cd $QT5BASE
git submodule foreach git fetch
git submodule foreach git checkout master
git submodule foreach git rebase origin/master
