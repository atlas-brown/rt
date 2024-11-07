#!/bin/bash

#################################
##
## Start of editable area

TELEGRAM_CHAT_ID="$(cat /root/.secrets/tg-chatid.txt)"
TELEGRAM_BOT_TOKEN="$(cat /root/.secrets/tg-token.txt)"
APT_UPGRADE_CMD="upgrade"          # choose between 'upgrade' or 'dist-upgrade' (only relevant on deb-based OS)
MAX_MESSAGE_LENGTH=2400
RETRIES=10
WAIT_TIME=5
OUTPUT_TARGET="/var/log/systemUpgradeTelegram.log"        # alternatively "/dev/stdout"
NO_REBOOT=false
CHECK_REQUIRED_REBOOT="/root/Scripts/requiredreboot.sh"
REQUIRED_REBOOT_STRING="! Reboot required !"

## End of editable area
##
################################


HEADER="*$(hostname) - $(date '+%d.%m.%Y %H:%M' 2> /dev/null)*
-------------------------------------------"

help() {
    echo    "This script runs system updates and can automatically choose between pacman and apt-get,"
    echo -e "depending on which binary actually exists on this machine.\n"
    echo    "Make sure to configure variables TELEGRAM_CHAT_ID & TELEGRAM_BOT_TOKEN in script first!"
    echo    "By default two plain text files are expected to only contain the ID of the Telegram chat"
    echo    "and the bot's token in: /root/.secrets/tg-chatid.txt and /root/.secrets/tg-token.txt"
    echo -e "\nThe script runs either:"
    echo    "  * pacman -Syu --noconfirm [ --ignore <package name(s)> ]"
    echo -e "  * apt-get -y -q $APT_UPGRADE_CMD  # choose between 'upgrade' and 'dist-upgrade' in vars\n"
    echo    "Additional options are: "
    echo    "  -h | --help                 this output"
    echo    "  --ignore <package name(s)>  (pacman only) don't update comma-seperated list of packages"
    echo    "  --sudo                      run with sudo. Make sure sudo runs without password prompt!"
    echo    "  --console                   print update information also to console for possibly"
    echo -e "                              configured mail notification of cron\n"

    exit 0
}

ERRORCODE=0
PRINT_TO_STDOUT=0
REBOOT_REQUIRED=false
PACMAN_APPENDAGE=""
OPTIONAL_SUDO=""

for ((i=1;i<=$#;i++)); do
    if [ ${!i} = "--help" ] || [ ${!i} = "-h" ]; then
        help
    elif [ ${!i} = "--ignore" ]; then
        ((i++))
        if [ -n "${!i}" ]; then PACMAN_APPENDAGE=" --ignore ${!i}"; fi
    elif [ ${!i} = "--console" ]; then
        PRINT_TO_STDOUT=1
    elif [ ${!i} = "--sudo" ]; then
        OPTIONAL_SUDO="sudo --non-interactive "
    fi
done

which apt-get 1> /dev/null 2>&1
RC=$?

if [ $RC -eq 0 ]; then
    apt-get update 1> /dev/null 2>&1
    if [ $? -ne 0 ]; then ERRORCODE=1; fi
    UPGRADE_CMD="apt-get -y -q ${APT_UPGRADE_CMD}"
else
    which pacman 1> /dev/null 2>&1
    RC=$?
    if [ $RC -eq 0 ]; then
        UPGRADE_CMD="pacman -Syu --noconfirm"
    else
        ERRORCODE=2
    fi
fi

if [ $ERRORCODE -eq 0 ]; then
    template="${HEADER}
*'${OPTIONAL_SUDO}${UPGRADE_CMD}${PACMAN_APPENDAGE}'*
$(${OPTIONAL_SUDO}${UPGRADE_CMD}${PACMAN_APPENDAGE} 2>> /dev/stdout | grep -vE "downloading|^Get:|^Preparing to unpack|^Unpacking |\[Y/n\]|checking|upgrading [-a-zA-Z0-9]+...|\(Reading database ... [0-9]*%|^Inst |^Conf ")
"

elif [ $ERRORCODE -eq 1 ]; then
    template="${HEADER}

*Error:*
command 'apt-get update' failed"

else
    template="${HEADER}

*Error:*
Could not find apt-get or pacman"

fi

if [ $PRINT_TO_STDOUT -eq 1 ]; then
    echo "$template" >> "$OUTPUT_TARGET"
fi


# check if the variable contains a path to an executable script which could check for a required reboot
if [ -x "${CHECK_REQUIRED_REBOOT}" ]; then
    # executing the script which checks for required reboot. This script must return exit code 1 in case 
    # a reboot is required and also an information as string on stdout, which will be checked here.
    # These two prerequesits should avoid reboots by mistake.
    result=$(${CHECK_REQUIRED_REBOOT} 2> /dev/null)
    rc=$?

    # The variable REQUIRED_REBOOT_STRING can be configured in the header and should contain the string
    # which the reboot check script returns in case of a required reboot. It will be checked here, if 
    # that string was returned.
    result=$(echo "$result" | grep -o "${REQUIRED_REBOOT_STRING}")
    if [ $rc -eq 1 ] && [ "$result" == "$REQUIRED_REBOOT_STRING" ]; then 
        REBOOT_REQUIRED=true
    fi
fi

# Add an information about the required reboot and that the reboot will be initiated when this script
# here finishes
if [ "$REBOOT_REQUIRED" == "true" ] && [ "$NO_REBOOT" == "false" ]; then
    template="${template}

ATTENTION! A reboot is required! 
Rebooting ..."
fi

# Telegram messages are not successfully sent when the message contains underscores. Therefore escaping them:
template=$(echo "$template" | sed -e 's|_|\\_|g' -e 's|+|\\+|g' -e 's/ *\[\]//g' -e 's|\[|\\[|g' )

message_chars=$(echo "$template" | wc -m)

declare -a message_array
array_index=0

if [ $message_chars -gt $MAX_MESSAGE_LENGTH ]; then
    char_count=0
    while read  line; do
        char_count=$(($char_count + $(echo "$line" | wc -m) ))

        if [ $char_count -ge $MAX_MESSAGE_LENGTH ]; then
            array_index=$(($array_index + 1))
            char_count=$(echo "$line" | wc -m)
        fi

	line="$(echo "$line" | awk '{gsub(/.{80}/,"&\n")}1')"

        if [ -n "${message_array[${array_index}]}" ]; then
            message_array[${array_index}]="${message_array[${array_index}]}
$line"
        else
            message_array[${array_index}]="Part: $((${array_index} + 1))
$line"
        fi

    done <<< "$template"
else
    message_array[0]="$template"
fi

index=0

while [ $index -le $array_index ]; do
    echo " " >> "$OUTPUT_TARGET"
    echo "======== SENDING: =======" >> "$OUTPUT_TARGET"
    echo "index: $index" >> "$OUTPUT_TARGET"
    echo " " >> "$OUTPUT_TARGET"
    echo "${message_array[$index]}" >> "$OUTPUT_TARGET"
    echo " " >> "$OUTPUT_TARGET"

    attempt=0

    while [ $attempt -lt $RETRIES ]; do
        curl_output=$(/usr/bin/curl --silent \
                     --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
                     --data-urlencode "text=${message_array[$index]}" \
                     --data-urlencode "parse_mode=Markdown" \
                     --data-urlencode "disable_web_page_preview=true" \
                     "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage")

        error_code=$?

        # the api returns "ok":true, or "ok":false,
        api_success=$( echo "$curl_output" | grep -Eo '{"ok":[^,]+' | sed 's|^.*:||' )


        if [ $error_code -eq 0 ] && [ "$api_success" = "true" ]; then
            break
        fi

        if [ $PRINT_TO_STDOUT -eq 1 ]; then 
            echo "-------------------------------------------" >> "$OUTPUT_TARGET"
            PRINT_TO_STDOUT=0
        fi

        if [ "$api_success" = "false" ]; then
            echo "ERROR: API returned state 'false'. Telegram message was not sent. Full API response:" >> "$OUTPUT_TARGET"
            # mask username and names from within telegram
            curl_output=$(echo "$curl_output" | sed -e 's|\("[a-zA-Z_]*name":"\)[^"]*"|\1***REMOVED***"|g' )
            echo "$curl_output" >> "$OUTPUT_TARGET"
            break
        fi

        if [ $error_code -ne 0 ]; then
            echo "Error sending Telegram message. curl returned: $error_code" >> "$OUTPUT_TARGET"
            echo "Retries: $(($attempt + 1)) out of $RETRIES" >> "$OUTPUT_TARGET"
        fi

        attempt=$(($attempt + 1))
        # When sending failed, wait a few seconds (see variable value in the header) and try again to send message
	sleep $WAIT_TIME
    done
    index=$(($index + 1))
    sleep $WAIT_TIME # to make sure the messages are received in the correct order
done

if [ "$REBOOT_REQUIRED" == "true" ] && [ "$NO_REBOOT" == "false" ]; then
    /sbin/reboot
fi
