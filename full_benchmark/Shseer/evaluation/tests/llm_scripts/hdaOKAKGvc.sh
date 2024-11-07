
#!/bin/sh

if [ -f $1 ]; then
    rows=$(cat $1 | wc -l)
    columns=$(head -n 1 $1 | tr ',' '\n' | wc -l)
    echo "Number of rows: $rows"
    echo "Number of columns: $columns"
else
    echo "File does not exist"
fi
