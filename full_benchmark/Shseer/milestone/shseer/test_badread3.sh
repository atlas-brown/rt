#!/bin/sh

f () {
    CURFILE="sample2.csv"
    python3 run.py $CURFILE
    rm "$CURFILE"

}
CURFILE="sample1.csv"
echo "Preview of samples..."
f
# will fail as CURFILE=sample2.csv has been deleted by the function f
head "$CURFILE"