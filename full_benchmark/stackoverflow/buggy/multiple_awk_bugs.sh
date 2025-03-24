#!/bin/sh
# https://stackoverflow.com/questions/48144452/add-filename-to-output-of-an-xargs-and-awk-command

# ---
# tags:   buggy, line_annot, awk
# intent: do some stuff (doesn't matter) and print '<filename> <date> <number>' for each file
# bug:    FILE is not defined in 'awk' (second pipeline)
# bug:    'xargs' does not have a '-c' option (third pipeline)
# bug:    unwanted substitution in subshell ($1 and $2 must be escaped) (fourth pipeline)
# bug:    output is split in two lines (fourth pipeline)
# ---

# should be correct (assuming file do not contain spaces)
find ./ -name "*.txt" | xargs -I FILE awk '{if(max<$2){max=$2;datum=$1}}END{print datum, max}' FILE >> out.txt

find ./ -name "*.txt" | xargs -I FILE echo FILE | awk '{if(max<$2){max=$2;datum=$1}}END{print datum, max}' FILE >> out.txt

find ./ -name "*.txt" | xargs -I FILE -c "echo FILE ; awk '{if(max<$2){max=$2;datum=$1}}END{print datum, max}' FILE" >> out.txt

# @output ".*[^\n] [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]+"
# stream enable
find ./ -name "*.txt" -exec sh -c "echo {} && awk '{if(max<$2){max=$2;datum=$1}}END{print datum, max}' {}" \; >> out.txt
