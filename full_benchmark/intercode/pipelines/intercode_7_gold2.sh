# Query: Check if the current shell is running within a 'screen' process and print "True" or "False"

ps -o comm= $(pstree -sp $$ | awk -F '[^0-9]*' '{print $2}') | grep -q 'screen' && echo "True" || echo "False"