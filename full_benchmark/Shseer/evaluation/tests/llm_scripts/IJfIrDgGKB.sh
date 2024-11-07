
#!/bin/sh

if [ -d $1 ] && [ -d $2 ]; then
    diff $1 $2 > diff_report.txt
else
    echo "One or both directories do not exist"
fi
