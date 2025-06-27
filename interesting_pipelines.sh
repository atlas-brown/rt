# match . \ / | [ ] $ ( ) { } ? + * ^ only if they are escaped (e.g match \. but not ., match \? but not ?)
# @output "(\\[]\\.|$(){}?+*^/]|[^]\\.|$(){}?+*^/])*"
# stream enable
    echo $* | sed "s/[]\\.|$(){}?+*^]/\\\\&/g" | sed "s/\\//\\\\\//g"

# @output "~([0-9]*: | master |@.*|: <.*)UP~( master |@.*|: <.*)"
# stream enable
    interfaces="$(ip link show | sed "/ master /d;/UP/!d;s/^[0-9]*: //g;s/@.*//g;s/: <.*//g;")"


################################################################################
# Commit message: rake-fast: remove brackets from completion entries  Fixes #5653
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/c56fa996e7cb1500dca97723d525e4c97af33c75
# Category: 
# Notes: 
# Changed content:
# - rake --silent --tasks | cut -d " " -f 2 > .rake_tasks
# + rake --silent --tasks | cut -d " " -f 2 | sed 's/\[.*\]//g' > .rake_tasks
################################################################################
# https://www.rubyguides.com/2019/02/ruby-rake/
# https://chatgpt.com/c/67fa811b-aa9c-8006-96a6-71976dee2069
# I'm not sure if the developers were aware of the existence of brackets in the output or not.
# @assume "rake --silent --tasks" --> "rake [a-z:]+(\[[^ ]*\])?"
# @output "[a-z:]+"
# stream enable
  rake --silent --tasks | cut -d " " -f 2 | sed 's/\[.*\]//g' > .rake_tasks


################################################################################
# Commit message: Better IPv4 detection (#278) On some systems like Hetzner VM cloud i have a Point-to-Point interface so i have a peer address on the same line as my public IPv4 (look at peer here : https://linux.die.net/man/8/ip )  An example of `ip a` with peer is :  ``` 2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000     link/ether 96:00:00:a2:88:c2 brd ff:ff:ff:ff:ff:ff     altname enp0s3     inet XX.XX.XX.XX peer XX.XX.XX.XX/32 brd XX.XX.XX.XX scope global eth0        valid_lft forever preferred_lft forever     inet6 fe80::9400:ff:fea2:88c2/64 scope link         valid_lft forever preferred_lft forever ``` With a peer, the output of the command line 74 is : `XX.XX.XX.XX peer XX.XX.XX.XX` I just modify this line with awk to print only the first field which is always the IPv4. I think it's correct and it's work like a charm when there is a peer or not now. But tell me if it's not good for you :) Thanks for your work !
# Commit URL: https://github.com/angristan/wireguard-install/commit/e05e633014628a65942cffab66f68228b6e17f7a
# Category: 
# Notes: 
# Changed content:
# - SERVER_PUB_IP=$(ip -4 addr | sed -ne 's|^.* inet \([^/]*\)/.* scope global.*$|\1|p' | head -1)
# + SERVER_PUB_IP=$(ip -4 addr | sed -ne 's|^.* inet \([^/]*\)/.* scope global.*$|\1|p' | awk '{print $1}' | head -1)
################################################################################
# This could probably be caught if "ip -4 addr" was modeled
# Commit message explains the problem quite nicely
# @assume "ip -4 addr" --> ".* inet ([0-9]{1,3}\.){3}\.[0-9]{1,3}( peer ([0-9]{1,3}\.){3}\.[0-9]{1,3})? ([^ \t]+)+ scope global [^ \t]+"
# @output "([0-9]{1,3}\.){3}\.[0-9]{1,3}"
# stream enable
	SERVER_PUB_IP=$(ip -4 addr | sed -ne 's|^.* inet \([^/]*\)/.* scope global.*$|\1|p' | awk '{print $1}' | head -1)


# @output "www.google.com"
echo "http://www.google.com" | sed -E 's|https?://([^/]+).*|\1|'



# Source: full_benchmark/pash_benchmark/benchmarks/teraseq/5TERA3/run_5TERA3.sh
# Commands: cut, paste, sed

# annotation1:
# @assume: "zcat ${sdir}/fastq/tmp.wo_rel3.fastq.gz" --> "("\ 
# "@[A-Z]:[0-9]+:[0-9]+-[0-9A-Z:]+ [0-9A-Z:]+\n"\
# "[AGCT]+\n"\
# "+\n"\
# "[A-Z]+\n"\
# ")*"
# @output: "([A-Z]:[0-9]+:[0-9]+-[0-9A-Z:]+ [0-9A-Z:]+\n)*"

# annotation2:
# @assume: "zcat ${sdir}/fastq/tmp.wo_rel3.fastq.gz" --> "("\ 
# "@[A-Z]:[0-9]+:[0-9]+-[0-9A-Z:]+\t[0-9A-Z:]+\n"\
# "[AGCT]+\n"\
# "+\n"\
# "[A-Z]+\n"\
# ")*"
# @output: "([A-Z]:[0-9]+:[0-9]+-[0-9A-Z:]+\n)*"


# annotation3:
# @assume: "zcat ${sdir}/fastq/tmp.wo_rel3.fastq.gz" --> "("\ 
# "@[A-Z]:[0-9]+:[0-9]+-[0-9A-Z:]+\t[0-9A-Z:]+\n"\
# "[AGCT]+\n"\
# "[A-Z]+\n"\
# ")*"
# @output: "(([A-Z]:[0-9]+:[0-9]+-[0-9A-Z:]+|[AGCT]+|[A-Z]+)\n)*"

# annotation4:
# @assume: "zcat ${sdir}/fastq/tmp.wo_rel3.fastq.gz" --> \
# "FASTQ\n"\
# "("\ 
# "@[A-Z]:[0-9]+:[0-9]+-[0-9A-Z:]+ [0-9A-Z:]+\n"\
# "[AGCT]+\n"\
# "+\n"\
# "[A-Z]+\n"\
# ")*"
# @output: "FASTQ\n(([A-Z]:[0-9]+:[0-9]+-[0-9A-Z:]+ [0-9A-Z:]+|[AGCT]+|[A-Z]+)\n)*"
zcat "${sdir}"/fastq/tmp.wo_rel3.fastq.gz | paste - - - - | cut -f1 | sed "s/^@//g"

# annotation1:
# @assume: "cat ${1}" --> "[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2},(login|logout),[a-zA-Z0-9_]+"
# @assert: "cut -d "," -f 1" --> "[0-9]{4}-[0-9]{2}-[0-9]{2}"


# annotation2:
# @assume: "cat ${1}" --> "[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}T[0-9]{1,2}:[0-9]{2}:[0-9]{2},(login|logout),[a-zA-Z0-9_]+"
# @assert: "cut -d "," -f 1" --> "[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}|[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}T[0-9]:[0-9]{2}:[0-9]{2}"
cat "${1}" | sed "s/T..:..:..//" | cut -d "," -f 1,3 | sort -u | cut -d "," -f 1 | sort | uniq -c | awk "{print \$2,\$1}"


# annotation1:
# @assume: "curl -sI https://github.com/pi-hole/FTL/releases/latest" --> \
# "HTTP/2 302\r\n"\
# "content-type: text/html; charset=utf-8\r\n"\
# "location: https://github.com/pi-hole/FTL/releases/tag/v[0-9]+\.[0-9]+\.[0-9]+\r\n"\
# "server: github.com\r\n"
# @assert (whole stream): "v[0-9]+\.[0-9]+\.[0-9]+"

# annotation2:
# @assume: "curl -sI https://github.com/pi-hole/FTL/releases/latest" --> \
# "HTTP/2 302\r\n"\
# "content-type: text/html; charset=utf-8\r\n"\
# "location: https://github.com/pi-hole/FTL/releases/tag/v[0-9]+\.[0-9]+\.[0-9]+\r\n"\
# "content-location: https://github.com/pi-hole/FTL/releases/download/v[0-9]+\.[0-9]+\.[0-9]+/FTL\.tar\.gz\r\n"\
# "server: github.com\r\n"
# @assert (whole stream): "v[0-9]+\.[0-9]+\.[0-9]+FTL\.tar\.gz"
curl -sI https://github.com/pi-hole/FTL/releases/latest | grep --color=never -i Location | awk -F / '{print $NF}' | tr -d '[:cntrl:]'