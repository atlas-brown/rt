# Query: Remove leading and trailing spaces or tabs from "  Hello world!	  "

# @assume "echo -n \"  Hello world!    \"" --> "[ ]+Hello world![ ]+"
echo -n "  Hello world!    " | sed 's/^[ \t]*//;s/[ \t]*$//'
