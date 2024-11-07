
#!/bin/sh

recipient_email=$1
subject=$2
body=$3
attachment=$4

# Encode the attachment for email transmission
encoded_attachment=$(uuencode $attachment $(basename $attachment))

# Send the email with the attachment
(echo "$body"; echo ""; cat $encoded_attachment) | mail -s "$subject" $recipient_email
