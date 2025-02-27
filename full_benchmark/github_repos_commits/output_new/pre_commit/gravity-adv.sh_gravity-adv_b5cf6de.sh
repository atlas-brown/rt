#!/bin/bash
# The Pi-hole now blocks over 140,000 ad domains
# Address to send ads to (the RPi)
piholeIP="127.0.0.1"
# Optionally, uncomment to automatically detect the address.  Thanks Gregg
#piholeIP=$(ifconfig eth0 | awk '/inet addr/{print substr($2,6)}')

# Config file to hold URL rules
eventHorizion="/etc/dnsmasq.d/adList.conf"

echo "Getting yoyo ad list..." # Approximately 2452 domains at the time of writing
curl -s -d mimetype=plaintext -d hostformat=unixhosts http://pgl.yoyo.org/adservers/serverlist.php? | sort > /tmp/matter.txt
echo "Getting winhelp2002 ad list..." # 12985 domains
curl -s http://winhelp2002.mvps.org/hosts.txt | grep -v "#" | grep -v "127.0.0.1" | sed '/^$/d' | sed 's/\ /\\ /g' | awk '{print $2}' | sort >> /tmp/matter.txt
echo "Getting adaway ad list..." # 445 domains
curl -s https://adaway.org/hosts.txt | grep -v "#" | grep -v "::1" | sed '/^$/d' | sed 's/\ /\\ /g' | awk '{print $2}' | grep -v '^\\' | grep -v '\\$' | sort >> /tmp/matter.txt
echo "Getting hosts-file ad list..." # 28050 domains
curl -s http://hosts-file.net/.%5Cad_servers.txt | grep -v "#" | grep -v "::1" | sed '/^$/d' | sed 's/\ /\\ /g' | awk '{print $2}' | grep -v '^\\' | grep -v '\\$' | sort >> /tmp/matter.txt
echo "Getting malwaredomainlist ad list..." # 1352 domains
curl -s http://www.malwaredomainlist.com/hostslist/hosts.txt | grep -v "#" | sed '/^$/d' | sed 's/\ /\\ /g' | awk '{print $3}' | grep -v '^\\' | grep -v '\\$' | sort >> /tmp/matter.txt
echo "Getting adblock.gjtech ad list..." # 696 domains
curl -s http://adblock.gjtech.net/?format=unix-hosts | grep -v "#" | sed '/^$/d' | sed 's/\ /\\ /g' | awk '{print $2}' | grep -v '^\\' | grep -v '\\$' | sort >> /tmp/matter.txt
echo "Getting someone who cares ad list..." # 10600
curl -s http://someonewhocares.org/hosts/hosts | grep -v "#" | sed '/^$/d' | sed 's/\ /\\ /g' | grep -v '^\\' | grep -v '\\$' | awk '{print $2}' | grep -v '^\\' | grep -v '\\$' | sort >> /tmp/matter.txt
echo "Getting Mother of All Ad Blocks list..." # 102168 domains!! Thanks Kacy
curl -A 'Mozilla/5.0 (X11; Linux x86_64; rv:30.0) Gecko/20100101 Firefox/30.0' -e http://forum.xda-developers.com/ http://adblock.mahakala.is/ | grep -v "#" | awk '{print $2}' | sort >> /tmp/matter.txt

# Sort the aggregated results and remove any duplicates
################################################################################
# Commit message: Fixes issue #2 whitelist support  Just put a file named whitelist.txt in your home folder.  This file should contain one domain per line that needs to be whitelisted.  If the file does not exists, the script will continue as normal.
# Commit URL: https://github.com/pi-hole/pi-hole/commit/b5cf6de4a317647a1ec622dee4e58a361b76b19e
# Category: 
# Notes: 
# Changed content:
# - echo "Removing duplicates and formatting to address=/<ad domain>/"$piholeIP
# - cat /tmp/matter.txt | sed $'s/\r$//' | sort | uniq | sed '/^$/d' | awk -v "IP=$piholeIP" '{sub(/\r$/,""); print "address=/"$0"/"IP}' > /tmp/andLight.txt
# + # Remove entries from the whitelist file if it exists at the root of the current user's home folder
# + if [[ -f $whitelist ]];then
# + 	echo "Removing duplicates, whitelisting, and formatting the list of domains..."
# + 	cat /tmp/matter.txt | sed $'s/\r$//' | sort | uniq | sed '/^$/d' | grep -v -x -f $whitelist | awk -v "IP=$piholeIP" '{sub(/\r$/,""); print "address=/"$0"/"IP}' > /tmp/andLight.txt
# + 	numberOfSitesWhitelisted=$(cat $whitelist | wc -l | sed 's/^[ \t]*//')
# + 	echo "$numberOfSitesWhitelisted domains whitelisted."
# + else
# + 	echo "Removing duplicates and formatting the list of domains..."
# + 	cat /tmp/matter.txt | sed $'s/\r$//' | sort | uniq | sed '/^$/d' | awk -v "IP=$piholeIP" '{sub(/\r$/,""); print "address=/"$0"/"IP}' > /tmp/andLight.txt
# + fi
################################################################################
# put stream annotation here
# stream enable
echo "Removing duplicates and formatting to address=/<ad domain>/"$piholeIP
cat /tmp/matter.txt | sed $'s/\r$//' | sort | uniq | sed '/^$/d' | awk -v "IP=$piholeIP" '{sub(/\r$/,""); print "address=/"$0"/"IP}' > /tmp/andLight.txt

# Count how many domains were added so it can be displayed to the user
numberOfAdsBlocked=$(cat /tmp/andLight.txt | wc -l | sed 's/^[ \t]*//')
echo "$numberOfAdsBlocked ad domains added to the blacklist"

# Turn the file into a dnsmasq config file
mv /tmp/andLight.txt $eventHorizion

# Restart DNS
service dnsmasq restart