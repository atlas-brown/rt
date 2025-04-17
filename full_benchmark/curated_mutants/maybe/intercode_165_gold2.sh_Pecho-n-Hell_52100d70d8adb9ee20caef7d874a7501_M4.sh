# @output "Hello world!"
echo "  Hello world!    " | sed "s/^[ \\t]*//;s/[ \\t]*\$//"
