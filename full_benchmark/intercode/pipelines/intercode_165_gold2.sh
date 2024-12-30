# Query: Remove leading and trailing spaces or tabs from "  Hello world!	  "

# @output "Hello World!"
echo -n "  Hello world!    " | sed 's/^[ \t]*//;s/[ \t]*$//'
