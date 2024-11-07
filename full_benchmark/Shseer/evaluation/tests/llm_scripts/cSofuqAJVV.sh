#!/bin/sh

for file in *.tar.gz
do
    tar -xzf $file
    if [ ! -d documents ]; then
        mkdir documents
    fi
    if [ ! -d images ]; then
        mkdir images
    fi
    mv *.doc documents
    mv *.jpg images
done
