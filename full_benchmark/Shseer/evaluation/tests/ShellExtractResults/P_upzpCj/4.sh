#!/bin/sh

./generate_parts.sh
find ./parts_tmp/ -regex .*ch.*\.html\$ | wpl -f ./fixchunk.pstar
