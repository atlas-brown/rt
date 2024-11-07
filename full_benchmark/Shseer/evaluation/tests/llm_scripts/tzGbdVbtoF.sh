
for dir in $(echo $PATH | tr ':' '\n')
do
    echo "Number of executable files in $dir: $(find $dir -maxdepth 1 -type f -executable | wc -l)"
done
