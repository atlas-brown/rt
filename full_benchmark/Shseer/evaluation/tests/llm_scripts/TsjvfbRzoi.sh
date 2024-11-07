
#!/bin/sh

if [ -e $2 ] ; then
    chmod $1 $2
else
    echo "File or directory does not exist"
fi
