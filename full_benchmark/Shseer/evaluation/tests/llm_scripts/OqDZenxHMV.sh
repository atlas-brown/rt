
#!/bin/sh

recipient=$1
subject=$2
body=$3
attachment=$4

mail -s "$subject" $recipient <<< "$body"
