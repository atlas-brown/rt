
#!/bin/sh

if [ -d $1 ] && [ -d $2 ]; then
    echo "Files and subdirectories in $1:"
    ls -lR $1
    echo "Files and subdirectories in $2:"
    ls -lR $2
    diff -r $1 $2
else
    echo "One or both directories do not exist."
fi
