# Query: Remove leading and trailing spaces or tabs from "  Hello world!	  "

echo '  Hello world!	  ' | sed -e 's/^[ \t]*//' | sed -e 's/[ \t]*$//'