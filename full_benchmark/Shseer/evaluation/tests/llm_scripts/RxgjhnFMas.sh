
#!/bin/sh

threshold=90
current=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')

if [ $current -gt $threshold ]; then
    echo "Disk space is below threshold. Sending email alert..."
    # send email alert
fi
