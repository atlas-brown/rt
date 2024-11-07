
#!/bin/sh

directory=$1
audit_log="permissions_audit.log"

for item in $(find $directory -type f -o -type d)
do
    if [ $item != "excluded_directory" ] && [ $item != "excluded_file" ]; then
        chmod 644 $item
        echo "Changed permissions of $item" >> $audit_log
    fi
done
