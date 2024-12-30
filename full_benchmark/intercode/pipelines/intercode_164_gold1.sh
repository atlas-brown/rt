# Query: Remove all characters except ";" and digits from the string "  Hello world;876	  "

# @output ";876"
echo '  Hello world;876	  ' | tr -cd ';0-9'
