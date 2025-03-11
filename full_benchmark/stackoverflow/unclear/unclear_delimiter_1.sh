#!/bin/sh
# https://stackoverflow.com/questions/48645159/how-to-extract-file-name-from-vsftpd-log-with-shell-script

# ---
# tags: buggy, delimiter_issue, unclear
# bug:  delimiter is also contained in values
# ---

# /var/log/vsftpd.log contents:
# Tue Feb  6 11:49:25 2018 [pid 13018] [xyz] OK UPLOAD: Client "1.2.3.4", "/filename.zip", 131072000 bytes, 19607.40Kbyte/sec
# Tue Feb  6 11:49:25 2018 [pid 13017] [xyz] OK UPLOAD: Client "1.2.3.4", "/filename.zip", 131072000 bytes, 24426.38Kbyte/sec
# Tue Feb  6 11:49:30 2018 [pid 13018] [xyz] OK UPLOAD: Client "1.2.3.4", "/filename.zip", 131072000 bytes, 25387.19Kbyte/sec

# ? not sure how to annotate this

tail -F /var/log/vsftpd.log | while read line; do
  if echo "$line" | grep -q 'OK UPLOAD:'; then
    line=$(echo "$line" | tr -s " ")
    # cut uses ',' as delimiter, but filenames might contain it
    filename=$(echo "$line" | cut -d, -f2)
    echo "$filename"
  fi
done
