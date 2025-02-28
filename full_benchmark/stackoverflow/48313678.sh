#!/bin/bash
# https://stackoverflow.com/questions/48313678/curl-invalid-character-n-in-string-literal

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

# @expect "tr -d '\040\011\012\015'" --> "([a-f0-9]{2})*"
msg_hex_wn=$(xxd -ps <<< "$msg")| tr -d '\040\011\012\015' # bug here
# fix: msg_hex_wn=$(xxd -ps <<< "$msg" | tr -d '\040\011\012\015')
echo "Message in hex - $msg_hex_wn"
echo "\n"
echo $(xxd  -ps <<< "$msg") | tr -d '\040\011\012\015'

# Signing the message in hex
# the same bug here but it's not in a pipeline
curl -X POST localhost:8545  -d "{\"jsonrpc\":\"2.0\",\"method\":\"eth_sign\",\"params\":[\"0x525c846b777d003048dbabd0f2dd677086839812\",\
\"$(xxd  -ps <<< "$msg") | tr -d '\040\011\012\015'\"\
],\"id\":5}"

read
