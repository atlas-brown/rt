#!/usr/bin/bash
LOG=/opt/nut/var/log/wd.log
TIMESTAMP=`date +%m-%d-%Y\ %H:%M:%S`

function mail_data() {
  touch ${filename}
  header='To: <insert-mail>@<insert-provider>.com
From: root@stormstone
Subject: UPS Warning
'
  echo "${header}" > ${filename}
  #echo ${1} >> ${filename}
  # command substitution only catches STDOUT
  echo "$(/opt/local/bin/upsc mustek@localhost 2>&1)" >> ${filename}
}

status=$(/opt/local/bin/upsc mustek@localhost 2>&1 | wc -l | awk '{ print $1 }')
filename="/tmp/$(date +%m%d%Y%H%M%S)"

if [ ${status} -lt 3 ]
then
  echo "${TIMESTAMP} process is dead, attempting restart" >> ${LOG}
  #mail_data && /usr/bin/cat ${filename} | /opt/local/bin/msmtp -a default <insert-mail>@<insert-provider>.com
  /usr/sbin/svcadm disable ups-nut
  sleep 2
  #svcadm enable svc:/site/ups-nut
  /usr/sbin/svcadm enable ups-nut
  #/opt/custom/share/svc/ups-nut.sh stop
  #sleep 1
  #/opt/custom/share/svc/ups-nut.sh start
else
  echo "${TIMESTAMP} process alive" >> ${LOG}
fi
