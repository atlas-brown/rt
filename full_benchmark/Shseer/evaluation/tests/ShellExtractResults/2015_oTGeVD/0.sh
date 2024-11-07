#!/bin/bash

python ez_setup.py --user

# Note: I had to add the local package bin folder to my path for this to work - in my case it was /home/mwest/.local/bin (Mint17).
easy_install --user EasyAI
rm *.zip
