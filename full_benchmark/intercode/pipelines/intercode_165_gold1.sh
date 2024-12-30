# Query: Remove leading and trailing spaces or tabs from "  Hello world!	  "

# @output "Hello World!"
echo '  Hello world!	  ' | sed -e 's/^[ \t]*//' | sed -e 's/[ \t]*$//'
