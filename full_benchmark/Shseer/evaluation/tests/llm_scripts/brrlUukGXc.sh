
if [ -z "$(ls -A $1)" ]; then
    rmdir -p $1
fi
