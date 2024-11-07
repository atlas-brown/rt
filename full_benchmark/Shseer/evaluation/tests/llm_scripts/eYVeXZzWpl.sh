
#!/bin/sh

if [ -f $1 ] ; then
    grep -oP "<$2>\K(.*?)(?=<\/$2>)" $1
else
    echo "XML file does not exist"
fi
