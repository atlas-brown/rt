#!/bin/bash

# 9.9:
# @assume "cat $1" --> "Communicate fasT,\nOr you risk being latE...\nThe party line's fulL,\nSo quick! grab a platE..."
cat $1 | tr -c '[a-z][A-Z]' '\n' | grep '[A-Z]' | sed 1d | sed 1d | sed 2d | sed 3d | sed 5d | tr -c '[A-Z]' '\n' | tr -d '\n'
