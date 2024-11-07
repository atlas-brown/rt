#!/bin/sh
echo "Content-type:image/jpeg"
echo 
SECOND=`date +%S | cut -b2`
cat /var/www/images/camtest0$SECOND.jpg