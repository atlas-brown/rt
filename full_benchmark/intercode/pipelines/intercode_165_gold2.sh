# Query: Remove leading and trailing spaces or tabs from "  Hello world!	  "

echo -n "  Hello world!    " | sed 's/^[ \t]*//;s/[ \t]*$//'