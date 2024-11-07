# quotes in quotes
tmp=/tmp/jo.$$
trap "rm -f $tmp; exit" 0 1 2 15

${JO:-jo} msg='"All'\''s Well", she said.'


