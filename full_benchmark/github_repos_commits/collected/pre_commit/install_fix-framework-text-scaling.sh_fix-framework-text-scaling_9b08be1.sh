################################################################################
# Commit message: Fix match and condition
# Commit URL: https://github.com/basecamp/omakub/commit/9b08be176e6a2ed77430825eac715047acfffd52
# Category: 
# Notes: 
# Changed content:
# - COMPUTER_MAKER=$(sudo dmidecode -t system | grep 'Manufacturer' | awk '{print $2}')
# + COMPUTER_MAKER=$(sudo dmidecode -t system | grep 'Manufacturer:' | awk '{print $2}')
################################################################################
# @assert "grep 'Manufacturer'" --> ".*Manufacturer:.*"
# stream enable
COMPUTER_MAKER=$(sudo dmidecode -t system | grep 'Manufacturer' | awk '{print $2}')
SCREEN_RESOLUTION=$(xrandr | grep '*+' | awk '{print $1}')

if [ "$COMPUTER_MAKER" == "Framework" && "$SCREEN_RESOLUTION" == "2256x1504" ]; then
	gsettings set org.gnome.desktop.interface text-scaling-factor 0.8
fi