
#!/bin/sh

# Check if all command line arguments are provided
if [ $# -ne 3 ]; then
  echo "Usage: $0 <recipient_email> <subject> <body>"
  exit 1
fi

recipient_email=$1
subject=$2
body=$3

# Send the email using the mail command
echo "$body" | mail -s "$subject" "$recipient_email"
