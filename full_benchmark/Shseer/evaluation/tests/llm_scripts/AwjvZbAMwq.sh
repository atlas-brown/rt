
#!/bin/sh

if [ -d $2 ] ; then
    chmod $1 $2
else
    echo "Directory does not exist"
fi
