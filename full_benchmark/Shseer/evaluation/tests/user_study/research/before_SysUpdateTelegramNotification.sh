#!/bin/bash

#################################
##
## Start of editable area

TELEGRAM_CHAT_ID="$(cat /root/.secrets/tg-chatid.txt)"
TELEGRAM_BOT_TOKEN="$(cat /root/.secrets/tg-token.txt)"
APT_UPGRADE_CMD="upgrade"          # choose between 'upgrade' or 'dist-upgrade' (only relevant on deb-based OS)
RETRIES=10

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
    echo -e "  * apt -y -q $APT_UPGRADE_CMD  # choose between 'upgrade' and 'dist-upgrade' in vars\n"
    echo    "Additional options are: "
    echo    "  -h | --help                 this output"
    echo    "  --ignore <package name(s)>  (pacman only) don't update comma-seperated list of packages"
    echo    "  --sudo                      run with sudo. Make sure sudo runs without password prompt!"
    echo    "  --console                   print update information also to console for possibly"
    echo -e "                              configured mail notification of cron\n"

    exit 0
}

ERRORCODE=0
PRINT_TO_SDTOUT=0
PACMAN_APPENDAGE=""
OPTIONAL_SUDO=""

for ((i=1;i<=$#;i++)); do
    if [ ${!i} = "--help" ] || [ ${!i} = "-h" ]; then
        help
    elif [ ${!i} = "--ignore" ]; then
        ((i++))
        if [ -n "${!i}" ]; then PACMAN_APPENDAGE=" --ignore ${!i}"; fi
    elif [ ${!i} = "--console" ]; then
        PRINT_TO_SDTOUT=1
    elif [ ${!i} = "--sudo" ]; then
        OPTIONAL_SUDO="sudo --non-interactive "
    fi
done

which apt-get 1> /dev/null 2>&1
RC=$?

if [ $RC -eq 0 ]; then
    apt update 1> /dev/null 2>&1
    if [ $? -ne 0 ]; then ERRORCODE=1; fi
    UPGRADE_CMD="apt -y ${APT_UPGRADE_CMD}"
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

$(${OPTIONAL_SUDO}${UPGRADE_CMD}${PACMAN_APPENDAGE} 2>> /dev/stdout | grep -vE "downloading|\[Y/n\]|checking|upgrading [-a-zA-Z0-9]+...|\(Reading database.*\$" | sed 's/_/\_/g')
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

if [ $PRINT_TO_SDTOUT -eq 1 ]; then
    echo "$template"
fi

i=0
while [ $i -lt $RETRIES ]; do
    # Telegram messages are not successfully sent when the message contains underscores. Therefore escaping them:
    template=$(echo "$template" | sed 's|_|\\_|g')
    output=$(/usr/bin/curl --silent --output /dev/null \
             --data-urlencode "chat_id=${TELEGRAM_CHAT_ID}" \
             --data-urlencode "text=${template}" \
             --data-urlencode "parse_mode=Markdown" \
             --data-urlencode "disable_web_page_preview=true" \
             "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage")

    error_code=$?
    if [ $error_code -eq 0 ]; then
        break
    else
        if [ $PRINT_TO_SDTOUT -eq 1 ]; then echo "-------------------------------------------"; fi
        echo "Error sending Telegram message. curl returned: $error_code"
        echo "Retries: $(($i + 1)) out of $RETRIES"
    fi
    i=$(($i + 1))
    sleep 5
done
