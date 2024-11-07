# jo as filter

# filter array
echo "[1,2,3,4]" | ${JO:-jo} -f - 6 8

# filter object
${JO:-jo} a=1 b=2 | ${JO:-jo} -f - c=42 d=3

# multi-stage pipeline
${JO:-jo} a=1 b=2 | ${JO:-jo} -f - c=42 d=3 | ${JO:-jo} -f - -d . stage.1=a stage.2=b

# filter from file
tmp=/tmp/jo.filter.$$
trap "rm -f $tmp; exit" 0 1 2 15

${JO:-jo} a=1 b=2 > $tmp
${JO:-jo} -f $tmp c=42 d=3 | ${JO:-jo} -f - -d . stage.1=a stage.2=b

# take initial object from file, and mods from stdin
echo "c=42
d=3" | ${JO:-jo} -f $tmp | ${JO:-jo} -f - -d . stage.1=a stage.2=b

# this command should NOT output keys "c" and "d"
${JO:-jo} a=1 b=2 | ${JO:-jo} -f - c=42 d=3 | ${JO:-jo} -f $tmp -d . stage.1=a stage.2=b

# filter non-collections (input basically ignored)
echo hi | tee $tmp | ${JO:-jo} -f - people="need people"
${JO:-jo} -f $tmp people="need people"
