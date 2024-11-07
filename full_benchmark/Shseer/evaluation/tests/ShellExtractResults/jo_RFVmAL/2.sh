# object from file
tmp=/tmp/jo.$$
trap "rm -f $tmp; exit" 0 1 2 15

${JO:-jo} -a eX whY Zed  > $tmp
${JO:-jo} name=Jane obj:=$tmp


