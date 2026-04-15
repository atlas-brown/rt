#!/bin/bash

# 10.1: count Turing award recipients while working at Bell Labs
# @assume "cat $1" --> "[0-9]{4}\t[A-Za-z \"'-]+\t(Male|Female)\t[A-Za-z ]+\t[A-Za-z ]*\t[0-9]{4}\t[A-Za-z ,().'-]+"
# @output " *[0-9]+"
cat $1 | sed 1d | grep 'Bell' | cut -f 2 | wc -l
