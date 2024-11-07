#!/bin/bash
# author: mailto://hyongbai@gmail.com
# github: https://github.com/hyongbai/shoturl

#This may expired
BITLY_ACCESS_TOKEN="b5b243586d57e7b322bed06b15ef1f9042ebf19f"

function    urlencode() {
    local length="${#1}"
    for (( i = 0; i < length; i++ )); do
        local c="${1:i:1}"
        case $c in
            [a-zA-Z0-9.~_-]) printf "$c" ;;
            *) printf '%%%02X' "'$c"
        esac
    done
}

function    urldecode() { 
    # urldecode <string>
    local url_encoded="${1//+/ }"
    printf '%b' "${url_encoded//%/\x}"
}

function    get_protocol()
{
    GET_PROTOCOL_URL=$1
    echo "${GET_PROTOCOL_URL%://*}"
}

function    get_net_addr()
{
    GET_NET_ADDR_URL=$1
    echo "${GET_NET_ADDR_URL#*://}"
}

function    colorize()
{
    echo -e "\033[;33;1m${1}\033[0m"
}

function    optimize_url()
{
    OPTIMIZE_URL="$1"
    NET_ADDR=`get_net_addr "$OPTIMIZE_URL"`
    PROTOCOL=`get_protocol "$OPTIMIZE_URL"`

    if [ $PROTOCOL != "https" ] && [ $PROTOCOL != "http" ]; then
        PROTOCOL="http"
    fi

    echo "`urlencode "${PROTOCOL}://${NET_ADDR}"`"
}

function    curl_net()
{
    echo `curl --connect-timeout ${CONNECT_TIMEOUT}   ${*} 2>/dev/null`
}

function    escape_slash_char()
{
    OLD_CHAR=$1 && [ "${OLD_CHAR}" ] && echo ${OLD_CHAR//\\\///}
}

function    get_ctrl()
{
    [ `uname` == "Darwin" ] && echo "⌘" && return
    echo "Ctrl"
}

###

function    sina_short()
{
    tURL="$1" && [ ! "$tURL" ] && return
    SINA_RESULT=`curl_net "http://api.t.sina.com.cn/short_url/shorten.json?source=2483680040&url_long=${tURL}"`
    echo ${SINA_RESULT}|awk -F\" '{print $4}'
}

function    baidu_short()
{
    tURL="$1" && [ ! "$tURL" ] && return
    BAIDU_SHORTURL=`curl_net "dwz.cn/create.php -d url=${tURL}"`
    echo `escape_slash_char "$(echo ${BAIDU_SHORTURL}|awk -F\" '{print $4}')"`
}

function    google_short()
{
    tURL="$1" && [ ! "$tURL" ] && return
    param="{\"longUrl\": \"$1\"}"
    GOOGLE_RESULT=`curl https://www.googleapis.com/urlshortener/v1/url -H 'Content-Type: application/json' -d "${param}" 2>/dev/null`
    GOOGLE_RESULT=`echo $GOOGLE_RESULT | grep "\"id\"\:" | awk -F"\"id\"\:" '{print $2}' | awk -F"\," '{print $1}' | awk -F"\"" '{print $2}'`
    echo $GOOGLE_RESULT
}

function    bitly_base_short()
{
    tURL="$1" && [ ! "$tURL" ] && return
    BITLY_API_URL="https://api-ssl.bitly.com/v3/shorten?format=json"
    BITLY_RESULT=`curl_net "${BITLY_API_URL}&domain=${2}&access_token=${BITLY_ACCESS_TOKEN}&longUrl=${tURL}"`
    BITLY_RESULT=`echo ${BITLY_RESULT}| awk -F\"url\": '{print $2}'|awk -F\" '{print $2}'`
    echo "`escape_slash_char $BITLY_RESULT`"
}

function    bitly_short()
{
    echo "`bitly_base_short "$1" "bit.ly"`"
}

function    jmp_short()
{
    echo "`bitly_base_short "$1" "j.mp"`"
}

function    angry_short()
{
    ANGRY_RESULT=`curl_net -X POST -d "u=${1}" 'https://angry.im/p/url'`
    echo "${ANGRY_RESULT}"
}

function shot()
{
    echo -e "shortening by ${1}\n\n        `colorize $(${2} "${3}")`\n"
}

###################
## functions END ##
###################

URL="${1}" && [ ! "$URL" ] && echo "Pls input a valid url" && exit
URL=`optimize_url "$URL"` && CONNECT_TIMEOUT=50

###################
##   init  END   ##
###################

echo
echo "------------------------------------------------------------------------------"
echo
echo "Using shoturl \"{URL ADDRESS}\" instead of shoturl {URL ADDRESS} is better"
echo
echo "    long press `get_ctrl` and double click url to browser"
echo
shot "sina" "sina_short" "$URL"
shot "baidu" "baidu_short" "$URL"
shot "angry.im" "angry_short" "$URL"
shot "bitly" "bitly_short" "$URL"
shot "j.mp" "jmp_short" "$URL"
# shot "google" "google_short" "$URL" # NOT AVAILABLE
echo
echo "------------------------------------------------------------------------------"
echo