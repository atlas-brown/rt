#!/bin/sh
# https://stackoverflow.com/questions/49403972/find-function-names-alone-in-all-files-with-a-given-extension

# ---
# tags: unclear
# ---

# unclear how to annotate this

find "$1" \
    -type f \
    -name *.c \
    -exec echo {} \; \
    -exec grep "(*)" {} \; |
        sed 's/{//g'
