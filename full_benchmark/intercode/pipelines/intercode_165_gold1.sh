# Query: Remove leading and trailing spaces or tabs from "  Hello world!	  "

# @assume "echo '  Hello world!	  '" --> "[ \t]+Hello world![ \t]+"
echo '  Hello world!	  ' | sed -e 's/^[ \t]*//' | sed -e 's/[ \t]*$//'
