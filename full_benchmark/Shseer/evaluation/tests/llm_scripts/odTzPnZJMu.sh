
#!/bin/sh

if [ -d $1 ] && [ -d $2 ]; then
    ls $1 > temp1.txt
    ls $2 > temp2.txt

    diff temp1.txt temp2.txt
else
    echo "One or both directories do not exist"
fi
