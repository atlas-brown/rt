#!/bin/sh
 set -euo pipefail
 IFS=$'\n\t'

source ~/bin/_DLABO/CONFIG.INI

function DLABO()
{

# File Info
echo '~~~~~~~~~~~~~~~~~~~Audio File Data~~~~~~~~~~~~~~';

ls *.m*;
read -p "Length in bytes for file: " -e TM4A 
M4A=$(echo $TM4A | tr -d "[:space:]")

BYTES=$(afinfo $M4A | grep "audio bytes" | grep -Eo '[0-9]{1,15}')
DUR=$(afinfo $M4A | grep "estimated duration" | grep -Eo '[0-9].{1,10}')

#### DROPBOX BIT THAT HAS ELUDED ME FOR MONTHS.
#### AUTOMATION IS HERE!

## Prior to grabbing the shared link, I'm going to call create_shared_link_with_settings to be safe.
(curl -X POST https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings \
  --header 'Authorization: Bearer ' \
  --header 'Content-Type: application/json' \
  --data '{"path":"/~'$Names'/'$M4A'"}' > /dev/null);


## Grabbing actual shared link
## If this fails I have no way of knowing. Sigh. More to do.

TEMPMFL=$(curl -X POST https://api.dropboxapi.com/2/sharing/get_shared_links \
  --header 'Authorization: Bearer ' \
  --header 'Content-Type: application/json' \
  --data '{"path":"/~'$Names'/'$M4A'"}' | jq -r .links[].url);
  
# file type audio/mp4a-latm auto added at generation.
MFL=$(echo "$TEMPMFL" | sed s/https.*com// | sed s/?.*//)

# Episode Information:
echo '~~~~~~~~~~~~~~~~~~~Episode Information~~~~~~~~~~~~~~';
EPSNO=$(afinfo $M4A | grep "File:" | grep -Eo '[0-9][0-9][0-9]')

read -p "Episode name: " -e EPSNM
read -p "Episode subtitle: " -e EPSSBT
read -p "Episode Summary: " -e EPSSUM

PS3="Explicit tag. Select from Yes(Explict), No(Not explict) or Clean: "
select XPLCT in Clean Yes No
do
  echo $XPLCT
break
done

# Keywords
read -p "Add keywords: " -e KYWRDS

# echo '~~~~~~~~~~~~~~~~~~~Date and Time~~~~~~~~~~~~~~';
DOW=$(date +"%a")
CDATE=$(date +"%d")
MNTH=$(date +"%b")
PYR=$(date +"%Y")
TME=$(date +"%H:%M:%S")


echo "~~~~~~~~~~~~~~~~~~~~RSS FEED~~~~~~~~~~~~~~~";

# ----------------- END DATA COLLECTION -------------------

# Math
EstDur=$(echo "($DUR+0.5)/1" | bc)

hours=$(echo "($EstDur/3600)" | bc)
minutes=$(echo "(($EstDur/60)%60)" | bc)
seconds=$(echo "($EstDur%60)" | bc)
# echo "00:$minutes:$seconds"
DRTN=$(printf "%02d:%02d:%02d\n" $hours $minutes $seconds)

# ------------------ XML GENERATOR PROPER -------------------
ex "$RSS" << EOF
/<\/channel>/d
/<\/rss>/d
w
q

EOF

cat << EOF >> "$RSS"
<item>
  <title>${EPSNO}: ${EPSNM}</title>
  <itunes:subtitle>${EPSSBT}</itunes:subtitle>
  <itunes:author>${AUTHR}</itunes:author>
  <itunes:summary>${EPSSUM}</itunes:summary>
  <enclosure url="https://dl.dropbox.com${MFL}?dl=1" length="${BYTES}" type="audio/x-m4a" />
  <guid>https://dl.dropbox.com${MFL}?dl=1</guid>
  <itunes:duration>${DRTN}</itunes:duration>
  <pubDate>${DOW}, ${CDATE} ${MNTH} ${PYR} ${TME} +0900</pubDate>
  <itunes:keywords>English, ${KYWRDS}</itunes:keywords>
  <itunes:explicit>${XPLCT}</itunes:explicit>
</item>

</channel>
</rss>

EOF

clear
}

trap DLABO EXIT
