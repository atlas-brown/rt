
#!/bin/sh

dataFile="database.txt"

case $1 in
    set)
        echo "$2=$3" >> $dataFile
        ;;
    read)
        grep "^$2=" $dataFile | cut -d= -f2
        ;;
    delete)
        sed -i "/^$2=/d" $dataFile
        ;;
    select)
        dataFile=$2
        ;;
esac
