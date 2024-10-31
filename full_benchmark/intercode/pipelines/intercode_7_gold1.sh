# Query: Check if the current shell is running within a 'screen' process and print "True" or "False"

pstree -s $$ | grep -q "screen" && echo "True" || echo "False"