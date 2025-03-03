#!/bin/bash
# https://stackoverflow.com/questions/48313678/curl-invalid-character-n-in-string-literal

# ---
# tags: buggy, line_annot
# bug:  'a=$(..) | ..' instead of 'a=$(.. | ..)'
# bug:  the same bug appears in a string passed to curl
# ---

# grabbing day and month from current date
D=$(gdate)
DAY=$(gdate -d "$D" '+%d')
MONTH=$(gdate -d "$D" '+%m')
YEAR=$(gdate -d "$D" '+%Y')

echo "Day: $DAY"
echo "Month: $MONTH"
echo "Year: $YEAR"

# prepare todays JSON message for attestation
a="SH_$YEAR$MONTH$DAY"
b="_324019325_1_10_001_00_test"
filename=$a$b
hash="test hash"
addl_data="test data"
tag="test tag"

msg=$filename$tag$addl_data$hash
echo "Prepared Message is - $msg"

# @expect "([a-f0-9]{2})*" --> "tr -d '\040\011\012\015'"
msg_hex_wn=$(xxd -ps <<< "$msg") | tr -d '\040\011\012\015'
# fix: msg_hex_wn=$(xxd -ps <<< "$msg" | tr -d '\040\011\012\015')

echo "Message in hex - $msg_hex_wn"
echo "\n"
# @expect "([a-f0-9]{2})*" --> "tr -d '\040\011\012\015'"
echo $(xxd  -ps <<< "$msg") | tr -d '\040\011\012\015'

# signing the message in hex
# ! the same bug here
curl -X POST localhost:8545  -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_sign\",\"params\":[\"0x525c846b777d003048dbabd0f2dd677086839812\",\
\"$(xxd  -ps <<< "$msg") | tr -d '\040\011\012\015'\"\
],\"id\":5}"

read
