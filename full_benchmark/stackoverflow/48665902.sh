#!/bin/sh
# https://stackoverflow.com/questions/48665902/ignoring-empty-lines-and-perform-sdiff

# intent: count how many lines have content in file t2 but are blank in t1,
#         EXCEPT for empty lines that get matched because t1 has ended (EOF)

# sdiff outputs <t1 line> [ <|>] <t2 line>
# where   means both have the same content
#       < means t1 has content while t2 is blank OR t1 is blank but t2 has ended
#       | means both have different content
#       > means t2 has content while t1 is blank OR t2 is blank but t1 has ended

# how do we express that?
# grep's input will not contain lines of the form '<whitespace> > <whitespace>'

# ^: start of line
# (?!.*>\s*$): negative lookahead of lines that end with '><whitespace>'
# .*: anything

# @expect "grep -c '[>]'" --> "^(?!.*>\s*$).*"
sdiff "$t1" "$t2" | grep -c '[>]'

# to understand the command and the desired behavior run it with files:

# t1:
# a
# b
#
# c
#

# t2:
# a
# f
#
#
#
#
# h
#

# notice how many '<empty> > <empty>' lines appear because t2 is longer
