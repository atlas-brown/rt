#!/bin/sh

cat *.log | grep "Recv"| cut -d":" -f10| cut -d"|" -f2 >offsets.txt
cat *.log | grep "Send" | cut -d":" -f6| cut -d"|" -f2 >>offsets.txt

