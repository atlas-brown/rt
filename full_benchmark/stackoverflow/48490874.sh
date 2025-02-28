#!/bin/bash
# https://stackoverflow.com/questions/48490874/insert-text-after-tabs

# this can be caught without annotations
# @expect "echo "/mnt/discon1     ext4     defaults     0       2"" --> ""
blkid |
    grep "/dev/sdb" |
    cut -d " " -f2 |
    sed 's/"//g' |
    echo "/mnt/discon1     ext4     defaults     0       2" >> fstab.bak
