
#!/bin/sh

directory=$1
extension=$2
exclude_dir=$3

find $directory -type f -name "*.$extension" -not -path "*/$exclude_dir/*"
