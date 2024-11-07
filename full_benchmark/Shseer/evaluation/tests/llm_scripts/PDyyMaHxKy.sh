
#!/bin/sh

# Check if the correct number of arguments is provided
if [ $# -lt 2 ]; then
  echo "Usage: $0 <action> <input_file>"
  exit 1
fi

action=$1
input_file=$2

# Perform the specified action on the input file
case $action in
  "remove")
    rm $input_file
    ;;
  "rename")
    echo "Enter new file name: "
    read new_name
    mv $input_file $new_name
    ;;
  "append")
    echo "Enter text to append: "
    read text
    echo $text >> $input_file
    ;;
  "overwrite")
    echo "Enter new content: "
    read new_content
    echo $new_content > $input_file
    ;;
  *)
    echo "Invalid action"
    exit 1
    ;;
esac

echo "Action $action performed on $input_file"
