
#!/bin/sh

dir1="/path/to/dir1"
dir2="/path/to/dir2"

if [ ! -d $dir1 ] || [ ! -d $dir2 ]; then
    echo "Directory does not exist"
    exit 1
fi

inotifywait -m -r -e create,modify,delete $dir1 | while read dir event file
do
    echo "$event: $file" >> $dir1.log
done

inotifywait -m -r -e create,modify,delete $dir2 | while read dir event file
do
    echo "$event: $file" >> $dir2.log
done
