#!/bin/bash

# 9.6: Follow the directions for grep
# @assume "cat $1" --> "Any Grouping by this fRiend,\nMakes each sentence quickly clear!\nTop and bottom, either end,\nSpacE-in five -- see friend apPear!"
cat $1 | tr ' ' '\n' | grep '[A-Z]' | sed 1d | sed 3d | sed 3d | tr '[a-z]' '\n' | grep '[A-Z]' | sed 3d | tr -c '[A-Z]' '\n' | tr -d '\n'
