# Query: Remove all characters except ";" and digits from the string "  Hello world;876	  "

# @output ";876"
# @assume "echo '  Hello world;876	  '" --> ".*[^;0-9].*"
# @assume "tr -cd ';0-9'" --> ";876"
echo '  Hello world;876	  ' | tr -cd ';0-9'
