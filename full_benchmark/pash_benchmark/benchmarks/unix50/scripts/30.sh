#!/bin/bash

# 9.8: TELE-communications
# @assume "cat $1" --> "Communicate fasT,\nOr you risk being latE...\nThe party line's fulL,\nSo quick! grab a platE..."
cat $1 | tr -c '[a-z][A-Z]' '\n' | grep '[A-Z]' | sed 1d | sed 2d | sed 3d | sed 4d | tr -c '[A-Z]' '\n' | tr -d '\n'
