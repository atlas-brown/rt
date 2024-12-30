#!/bin/bash

# 9.3: animal that used to decorate the Unix room
# @assume "cat $1" --> "FLying so high,\nAMong modern net's\nINspired world-view:\nGOod as it gets!"
# @output "FLAMINGO"
cat $1 | cut -c 1-2 | tr -d '\n'
