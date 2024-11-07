
#!/bin/sh

if [ -d $1 ] ; then
    for file in $1/*
    do
        # Decrypt file using $2 (key or method)
        # Example: openssl enc -d -aes-256-cbc -in $file -out decrypted_$file
    done
fi
