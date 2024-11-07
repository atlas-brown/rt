#!/bin/bash

BOLD="\e[1m"; ESC="\e[0m"; GREEN="\e[32m"; RED="\e[31m";

allip() {
    case $1 in
        -m) pubip -m && locip -m ;;
        -M) pubip -m && locip -M ;;
        "") pubip && echo && locip ;;
        *) echo -e $__allip_usage ;;
    esac
}

pubip() {
    TITLE="$BOLD""Public IP Address:""$ESC"

    while IFS= read -r line; do
        ip_info+=("$line")
    done < <(curl -s https://freegeoip.app/json/ | jq --raw-output '(.ip, .region_name, .country_name)')

    ip_address="${ip_info[0]}"; region="${ip_info[1]}"; country="${ip_info[2]}"

    case $1 in
        -M) echo $ip_address ;;
        -m) echo -e $TITLE && echo $ip_address ;;
	    "") echo -e $TITLE && echo -e "\t$ip_address\t($region, $country)" ;;
        *) echo -e $__pubip_usage ;;
    esac
}

locip() {
    TITLE=$BOLD"Local IP Address(es):"$ESC

    ifjson=`ip -family inet -json address show`
    readarray -td ',' ifnames < <(printf '%s' "`echo $ifjson | jq --raw-output '[.[].ifname] | join(",")'`")
    readarray -td ',' localaddrs < <(printf '%s' "`echo $ifjson | jq --raw-output '[.[].addr_info[].local] | join(",")'`")
    readarray -td ',' operstates < <(printf '%s' "`echo $ifjson | jq --raw-output '[.[].operstate] | join(",")'`")

    # Find the length of the longest string in each array for use in formatting the printed table.
    ifmaxlen=0; admaxlen=0; stmaxlen=0;
    for j in ${!ifnames[@]}; do
        [[ ${#ifnames[j]} -gt $ifmaxlen ]] && ifmaxlen=${#ifnames[j]}
        [[ ${#localaddrs[j]} -gt $admaxlen ]] && admaxlen=${#localaddrs[j]}
        [[ ${#operstates[j]} -gt $stmaxlen ]] && stmaxlen=${#operstates[j]}
    done

    case $1 in
        -d | -u | "")
            echo -e $TITLE

            for i in "${!ifnames[@]}"; do
                case $1 in
                    -d)
                        [[ "${operstates[$i]}" == "DOWN" ]] && \
                        printf "\t%-"$ifmaxlen"s\t %-"$admaxlen"s\t "$RED"DOWN"$ESC"\n" \
                        ${ifnames[$i]} ${localaddrs[$i]}
                        ;;
                    -u)
                        [[ "${operstates[$i]}" == "UP" ]] && \
                        printf "\t%-"$ifmaxlen"s\t %-"$admaxlen"s\t "$GREEN"UP"$ESC"\n" \
                        ${ifnames[$i]} ${localaddrs[$i]}
                        ;;
                    "")
                        case ${operstates[$i]} in
                            UP) STATUS_COLOR=$GREEN ;;
                            DOWN) STATUS_COLOR=$RED ;;
                            *) STATUS_COLOR="" ;;
                        esac
                        printf "\t%-"$ifmaxlen"s\t %-"$admaxlen"s\t "$STATUS_COLOR"%-"$stmaxlen"s"$ESC"\n" \
                        ${ifnames[$i]} ${localaddrs[$i]} ${operstates[$i]}
                        ;;
                esac
            done
            ;;

        -m) for i in "${!ifnames[@]}"; do printf "%-"$ifmaxlen"s\t %-"$admaxlen"s\n" ${ifnames[$i]} ${localaddrs[$i]}; done ;;
        -M) printf "%s\n" ${localaddrs[@]} ;;
        *) echo -e $__locip_usage ;;
    esac
}

__allip_usage="
Usage: allip [ -m ]\n
\t-m\tMinimal - Equivalent to \`pubip -m && locip -m\`.\n
\t-M\tExtra Minimal - Equivalent to \`pubip -M && locip -M\`."

__pubip_usage="
Usage: pubip [ -m ]\n
\t-m\tMinimal - Dont show IP address location.
\t-M\tExtra Minimal - Only show IP address."

__locip_usage="
Usage: locip [ OPTION ]\n
\t-d\tDown - Only show interfaces that are currently down.\n
\t-m\tMinimal - Only show interface name and address.\n
\t-M\tExtra Minimal - Only show interface address(es).\n
\t-u\tUp - Only show interfaces that are up."
