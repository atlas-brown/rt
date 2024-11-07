#!/usr/bin/bash
#
# Demonstrate that bash runs and can examine the environment
#
echo "--- Running bash in Rocket ---"
echo "------------------------------"
echo
echo "--- Environment ---"
echo
env
echo
echo "--- Root File System Contents ---"
echo
/usr/bin/find / -wholename /proc -prune -o -wholename /sys -prune -o -print
echo
echo "--- Proc File System Root ---"
echo
/usr/bin/ls /proc
echo
echo "--- Run complete ---"
exit
