#!/bin/bash

# 10.2: list Turing award recipients while working at Bell Labs
# @file "$1": "[0-9]{4}\t[A-Za-z \"'-]+\t(Male|Female)\t[A-Za-z ]+\t[A-Za-z ]*\t[0-9]{4}\t[A-Za-z ,().'-]+"
cat $1 | sed 1d | grep 'Bell' | cut -f 2
