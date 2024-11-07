#!/bin/bash
for i in $(cat files); do
    wget http://www.lojban.org/files/lojban-list/$i
done
