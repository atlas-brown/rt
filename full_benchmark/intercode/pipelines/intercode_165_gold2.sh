# Query: Remove leading and trailing spaces or tabs from "  Hello world!	  "

# @output "Hello world!"
# @assume "echo -n \"  Hello world!    \"" --> "[ ]+Hello world![ ]+"
# @assume "sed 's/^[ \t]*//;s/[ \t]*$//'" --> "Hello world!"
echo -n "  Hello world!    " | sed 's/^[ \t]*//;s/[ \t]*$//'
