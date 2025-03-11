#!/bin/sh
# https://stackoverflow.com/questions/49258486/sed-replace-string-in-file-unexpected-behavior-when-using-variable-in-shell-scri

# ---
# tags: unclear
# ---

# unclear what the bug is
# unclear how to annotate this

# carte_config.xml:
# <slaveserver>
#   <name>master1</name>
#   <hostname>CONTAINER_IP</hostname>
#   <port>8181</port>
# </slaveserver>

ip=$(ip a | grep -oE "\b([0-9]{1,3}\.){3}[0-9]{1,3}\b" | grep 172.17)
echo $ip
sed -i -e 's?CONTAINER_IP?'$ip'?' /pentaho-di/carte_config.xml
