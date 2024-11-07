
#!/bin/sh

if [ -f $1 ]; then
    fileSize=$(wc -c < $1)
    chunkSize=$2
    numChunks=$((fileSize / chunkSize))
    split -b $chunkSize $1 $3
else
    echo "Input file does not exist"
fi
