
#!/bin/sh

recipient=$1
subject=$2
body=$3

echo "$body" | mail -s "$subject" "$recipient"
