# Commit message: Don't forget to escape also the slash "/"
# Commit URL: https://github.com/pi-hole/pi-hole/commit/2061daa902f9dc0f56daccfb024eeaca3ea1398d
# Category: 
# Notes: 
# Changed content:
# - echo $* | sed "s/[]\\.|$(){}?+*^]/\\\\&/g"
# + echo $* | sed "s/[]\\.|$(){}?+*^]/\\\\&/g" | sed "s/\\//\\\\\//g"
################################################################################

# match . \ / | [ ] $ ( ) { } ? + * ^ only if they are escaped (e.g match \. but not ., match \? but not ?)
# @output "(\\[]\\.|$(){}?+*^/]|[^]\\.|$(){}?+*^/])*"
# stream enable
    echo $* | sed "s/[]\\.|$(){}?+*^]/\\\\&/g" | sed "s/\\//\\\\\//g"

################################################################################
# Commit message: Remove `@` and following character from interface name  Signed-off-by: RD WebDesign <github@rdwebdesign.com.br>
# Commit URL: https://github.com/pi-hole/pi-hole/commit/5cebceadda93ceb73038b6d248044933af2e0459
# Category: 
# Notes: 
# Changed content:
# - interfaces="$(ip link show | sed "/ master /d;/UP/!d;s/^[0-9]*: //g;s/: <.*//g;")"
# + interfaces="$(ip link show | sed "/ master /d;/UP/!d;s/^[0-9]*: //g;s/@.*//g;s/: <.*//g;")"
################################################################################

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
# @assume "ip -4 addr" --> ".* inet ([0-9]{1,3}\.){3}\.[0-9]{1,3}( peer ([0-9]{1,3}\.){3}\.[0-9]{1,3})? ([^ \t]+)+ scope global [^ \t]+"
# @output "([0-9]{1,3}\.){3}\.[0-9]{1,3}"
# stream enable
	SERVER_PUB_IP=$(ip -4 addr | sed -ne 's|^.* inet \([^/]*\)/.* scope global.*$|\1|p' | awk '{print $1}' | head -1)


# @output "www.google.com"
# Query: Extract host name part from "http://www.google.com"
# Source: intercode dataset
echo "http://www.google.com" | sed -E 's|https?://([^/]+).*|\1|'



# Source: full_benchmark/pash_benchmark/benchmarks/teraseq/5TERA3/run_5TERA3.sh
# Seems to be outdated, I cannot find it in the latest version of the benchmark
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


# Source: ./full_benchmark/pash_benchmark/benchmarks/covid-mts/scripts/1.sh


# Example input:
# 2020-01-20T14:18:44,2484,10110,Jan 20 2020 02:18:41:000PM,37.9837070,23.7348870
# 2020-01-20T14:18:44,2484,10150,Jan 20 2020 02:13:26:000PM,37.9853370,23.7313640
# 2020-01-20T14:18:45,3445,10014,Jan 20 2020 02:18:41:000PM,37.9796490,23.7343420
# 2020-01-20T14:18:45,3445,10012,Jan 20 2020 02:18:26:000PM,37.9925650,23.7315220
# 2020-01-20T14:18:45,3445,10011,Jan 20 2020 02:18:31:000PM,38.0012580,23.7408010
# 2020-01-20T14:18:45,3445,10008,Jan 20 2020 02:18:28:000PM,37.9799120,23.7333690
# 2020-01-20T14:18:46,2640,79177,Jan 20 2020 02:18:43:000PM,38.0138060,23.7203270
# 2020-01-20T14:18:47,1797,10194,Jan 20 2020 02:18:39:000PM,37.9800910,23.7354610
# 2020-01-20T14:18:48,1798,10121,Jan 20 2020 02:18:44:000PM,37.9893340,23.7090520
# 2020-01-20T14:18:49,1799,30254,Jan 20 2020 02:18:30:000PM,37.9755420,23.7338780
# 2020-01-20T14:18:50,1800,10144,Jan 20 2020 02:18:46:000PM,37.9848170,23.7405040

# annotation1:
# @assume: "cat ${1}" --> "[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2},(login|logout),[a-zA-Z0-9_]+"
# @assert: "cut -d "," -f 1" --> "[0-9]{4}-[0-9]{2}-[0-9]{2}"


# annotation2:
# @assume: "cat ${1}" --> "[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}T[0-9]{1,2}:[0-9]{2}:[0-9]{2},(login|logout),[a-zA-Z0-9_]+"
# @assert: "cut -d "," -f 1" --> "[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}|[0-9]{4}-[0-9]{1,2}-[0-9]{1,2}T[0-9]:[0-9]{2}:[0-9]{2}"
cat "${1}" | sed "s/T..:..:..//" | cut -d "," -f 1,3 | sort -u | cut -d "," -f 1 | sort | uniq -c | awk "{print \$2,\$1}"


################################################################################
# Commit message: Use the 'Location:' header only.  Signed-off-by: Dan Schaper <dan.schaper@pi-hole.net>
# Commit URL: https://github.com/pi-hole/pi-hole/commit/523f6501576f76bfcc7e5d3ddc3cf0a287089790
# Category: 
# Notes: 
# Changed content:
# - if ! FTLlatesttag=$(curl -sI https://github.com/pi-hole/FTL/releases/latest | grep --color=never -i Location | awk -F / '{print $NF}' | tr -d '[:cntrl:]'); then
# + if ! FTLlatesttag=$(curl -sI https://github.com/pi-hole/FTL/releases/latest | grep --color=never -i Location: | awk -F / '{print $NF}' | tr -d '[:cntrl:]'); then
################################################################################

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


################################################################################
# Commit message: fix nginx mode
# Commit URL: https://github.com/acmesh-official/acme.sh/commit/2b5e2d4760d7c3ec36f5af33dfa95d9077cd5966
# Category: 
# Notes: 
# Changed content:
# - for included in $(cat "$2" | tr "\t" " " | grep "^ *include *.*;" | sed "s/include //" | tr -d " ;"); do
# + for included in $(cat "$2" | tr "\t" " " | grep "^ *include *;" | sed "s/include //" | tr -d " ;"); do
################################################################################
# This is a wrong fix!
# annotation1:
# @assume: "cat $2" --> "\t*include /etc/nginx/conf\.d/.*\.conf;"
# @output "/etc/nginx/conf\.d/.*\.conf"
cat "${2}" | tr "\t" " " | grep "^ *include *;" | sed "s/include //" | tr -d " ;"


# Source: full_benchmark/pash_benchmark/benchmarks/unix50/scripts/30.sh
# 9.8: TELE-communications
# Exact input:
# Communicate fasT,
# Or you risk being latE...
# The party line's fulL,
# So quick! grab a platE...
# annotation1: directly use the input

# annotation2: relax and use [ and ] in the input
# @assume: "cat ${1}" --> "([a-zA-Z\[\].'!]+\n){4}"

# annotation3:
# @assume: "cat ${1}" --> ".*"

cat ${1} | tr -c "[a-z][A-Z]" "\n" | grep "[A-Z]" | sed 1d | sed 2d | sed 3d | sed 4d | tr -c "[A-Z]" "\n" | tr -d "\n"


# Source: full_benchmark/pash_benchmark/benchmarks/unix50/scripts/34.sh
# 10.3: extract Ritchie's username
# Example input:
# Year	Name	Gender	Citizenship	Second Citizenship	Born	Affiliation at the time of the award
# 2018	Yoshua Bengio	Male	Canada	 	1964	University of Montreal, Canada, Mila (Quebec's Artificial Intelligence Institute) and IVADO (the Institute for Data Valorization)
# 2018	Geoffrey Hinton	Male	Canada	 	1947	Google, Vector Institute and University of Toronto, Canada
# 2018	Yann LeCun	Male	France	 	1960	New York University, USA, and Facebook
# 2017	John Leroy Hennessy	Male	United States	 	1952	Stanford University, USA
# 1983	Dennis MacAlistair Ritchie	Male	United States	 	1941	Bell Telephone Laboratories
# 1983	Kenneth Lane Thompson	Male	United States	 	1943	Bell Telephone Laboratories

# annotation1: # I want to write a regex that ensures the output should contain Ritchie, but it is too complex

# annotation2:
# @assume: "cat ${1}" --> "Year\tName\tGender\tCitizenship\tSecond Citizenship\tBorn\tAffiliation at the time of the award\n(([0-9]+{4})\t[a-zA-Z ]+\t(Male|Female)\t(.+)\t( )*\t([0-9]+{4})\t(.+)\n)*"

# annotation3:
# @assume: "cat ${1}" --> "Year\tName\tGender\tCitizenship\tSecond Citizenship\tBorn\tAffiliation at the time of the award\n(([0-9]+{4})\t.+\t(Male|Female)\t(.+)\t( )*\t([0-9]+{4})\t(.+)\n)*"

cat ${1} | grep "Bell" | cut -f 2 | head -n 1 | fmt -w1 | cut -c 1-1 | tr -d "\n" | tr "[A-Z]" "[a-z]"

# Source: full_benchmark/pash_benchmark/benchmarks/unix50/scripts/36.sh
# 11.2: most repeated first name in the list?
# Example input:
# 2019	DAVID TSE	“For seminal contributions to wireless network information theory and wireless network systems.”
# 2018	ERDAL ARIKAN	“For contributions to information and communications theory, especially the discovery of polar codes and polarization techniques.”
# 2017	SHLOMO SHAMAI	“For fundamental contributions to information theory and wireless communications.”
# 2016	ABBAS EL GAMAL	“For contributions to network multi-user information theory and for wide ranging impact on programmable circuit architectures.”
# 2015	IMRE CSISZAR	“For contributions to information theory, informationtheoretic security, and statistics.”

# annotation1: We cannot model sort, so we cannot verify this spec
# @assume: "cat ${1}" --> "([0-9]+{4}\t "[A-Z ]+\t"For .+"\n)*"
cat ${1} | cut -f 2 | cut -d " " -f 1 | sort | uniq -c | sort -nr | head -n 1 | fmt -w1 | sed 1d



# Source: full_benchmark/pash_benchmark/benchmarks/unix50/scripts/9.sh
# 4.3: find pieces captured by Belle with a pawn
# Example input:
# 1.e4 Nf6 2.e5 Nd5 3.d4 d6 4.Nf3 dxe5 5.Nxe5 g6 6.g3 Bf5 7.c4 Nb4 8.Qa4+ N4c6 9.d5 Bc2 10.Qb5 Qd6 11.Nxc6 Nxc6 12.Nc3 Bg7 13.Qxb7 O-O 14.Qxc6 Qb4 15.Kd2 Be4 16.Rg1 Rfb8 17.Bh3 Bh6+ 18.f4 Qa5 19.Re1 f5 20.Qe6+ Kf8 21.b3 Bg7 22.Bb2 Bd4 23.g4 Rb6 24.Qd7 Rd6 25.Qa4 Qb6 26.Ba3 Bxc3+ 27.Kxc3 Rdd8 28.Rad1 Qf2 29.gxf5 Qc2+ 30.Kd4 gxf5 31.Qc6 Qf2+ 32.Ke5 Kg8 33.Rg1+ Kh8 34.Bxe7 Qb2+ 35.Rd4 Qg2 36.Qf6+ Kg8 37.Bxg2 Rxd5+ 38.Ke6 h6 39.Qxh6 Re5+ 40.fxe5 Rf8 41.Bf3# 1-0

cat ${1} | tr " " "\n" | grep "x" | grep "\." | cut -d "." -f 2 | grep -v "[KQRBN]" | wc -l


