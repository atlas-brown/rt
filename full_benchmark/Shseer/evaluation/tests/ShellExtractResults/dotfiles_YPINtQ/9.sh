#!/bin/sh

# Resizes an image to specified size
# (aspect ratio observed)
#
# Naming Convention: name@size.png
#
# $1 = filename
# $2 = original
# $3 = new
# $4 = extension
fn_resize() {
  sips -Z $3 $1@$2.$4 --out $1@$3.$4
}
