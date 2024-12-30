# Query: Remove all characters except ";" and digits from the string "  Hello world;876	  "

# @output ";876"
echo "  Hello world;876     " | sed 's/[^0-9;]//g'
