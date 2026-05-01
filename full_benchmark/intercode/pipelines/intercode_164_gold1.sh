# Query: Remove all characters except ";" and digits from the string "  Hello world;876	  "

# @assume "echo '  Hello world;876	  '" --> "  Hello world;876[ \t]+"
echo '  Hello world;876	  ' | tr -cd ';0-9'
