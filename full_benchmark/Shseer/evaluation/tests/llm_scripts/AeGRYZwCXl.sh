
#!/bin/sh

# Parse command line arguments
action=$1
key=$2
value=$3
file=${4:-database.txt}

# Perform action based on command line input
case $action in
    "set")
        echo "$key=$value" >> $file
        ;;
    "read")
        grep "^$key=" $file | cut -d '=' -f 2
        ;;
    "delete")
        sed -i "/^$key=/d" $file
        ;;
    *)
        echo "Invalid action. Supported actions: set, read, delete"
        ;;
esac
