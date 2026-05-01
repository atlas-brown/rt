#!/bin/bash

# 10.3: extract Ritchie's username
# @file "$1": "[0-9]{4}\t[A-Za-z \"'-]+\t(Male|Female)\t[A-Za-z ]+\t[A-Za-z ]*\t[0-9]{4}\t[A-Za-z ,().'-]+"
cat $1 | grep 'Bell' | cut -f 2 | head -n 1 | fmt -w1 | cut -c 1-1 | tr -d '\n' | tr '[A-Z]' '[a-z]'
