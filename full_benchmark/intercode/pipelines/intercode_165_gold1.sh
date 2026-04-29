# Query: Remove leading and trailing spaces or tabs from "  Hello world!	  "

# @output "Hello world!"
# @assume "echo '  Hello world!	  '" --> "[ \t]+Hello world![ \t]+"
# @assume "sed -e 's/[ \t]*$//'" --> "Hello world!"
echo '  Hello world!	  ' | sed -e 's/^[ \t]*//' | sed -e 's/[ \t]*$//'
