# Intercode

# @output "www.google.com"
# Query: Extract host name part from "http://www.google.com"
# Source: intercode dataset
# require support of references (\1)
echo "http://www.google.com" | sed -E 's|https?://([^/]+).*|\1|'


# Pash benchmark
# 7/22
# imprecise model
# Source: full_benchmark/pash_benchmark/benchmarks/covid-mts/scripts/5.sh
# example input:
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

# example output:
# 	2020-01-20
# 10011	1
# 10014	1
# 79177	1
# 30254	1
# 10121	1
# 10194	1
# 10008	1
# 10150	1
# 10110	1
# 10012	1

sed 's/T\(..\):..:../,\1/' <in.csv | awk -F, '
!seen[$1 $2 $4] { seen[$1 $2 $4] = 1; hours[$1 $4]++; bus[$4] = 1; day[$1] = 1; }
END {
   PROCINFO["sorted_in"] = "@ind_str_asc"
   for (d in day)
     printf("\t%s", d);
   printf("\n");
   for (b in bus) {
     printf("%s", b);
     for (d in day)
       printf("\t%s", hours[d b]);
     printf("\n");
   }
}' > out

# 7/22
# precise model
# example xargs curl output:
# <html>
#  <head>
#   <title>Index of /pub/data/noaa/2015</title>
#  </head>
#  <body>
# <h1>Index of /pub/data/noaa/2015</h1>
#   <table>
#    <tr><th><a href="?C=N;O=D">Name</a></th><th><a href="?C=M;O=A">Last modified</a></th><th><a href="?C=S;O=A">Size</a></th><th><a href="?C=D;O=A">Description</a></th></tr>
#    <tr><th colspan="4"><hr></th></tr>
# <tr><td><a href="/pub/data/noaa/">Parent Directory</a></td><td>&nbsp;</td><td align="right">  - </td><td>&nbsp;</td></tr>
# <tr><td><a href="007070-99999-2015.gz">007070-99999-2015.gz</a></td><td align="right">2021-02-05 00:23  </td><td align="right">1.9K</td><td>&nbsp;</td></tr>
# <tr><td><a href="010010-99999-2015.gz">010010-99999-2015.gz</a></td><td align="right">2021-02-05 00:23  </td><td align="right">303K</td><td>&nbsp;</td></tr>
# <tr><td><a href="010014-99999-2015.gz">010014-99999-2015.gz</a></td><td align="right">2021-02-05 00:23  </td><td align="right">199K</td><td>&nbsp;</td></tr>
# <tr><td><a href="010020-99999-2015.gz">010020-99999-2015.gz</a></td><td align="right">2021-02-05 00:23  </td><td align="right">150K</td><td>&nbsp;</td></tr>
# <tr><td><a href="010030-99999-2015.gz">010030-99999-2015.gz</a></td><td align="right">2021-02-05 00:23  </td><td align="right">264K</td><td>&nbsp;</td></tr>
#    <tr><th colspan="4"><hr></th></tr>
# </table>
# </body></html>

seq ${FROM} ${TO} | sed "s;^;${URL};" | sed "s;$;/;" | xargs -n1 -r curl --insecure | grep gz | sed "s;.*\"\\(.*\\)\\(20[0-9][0-9]\\).gz\".*;${URL}\2/\1\2.gz;" | tail -n +${sample_starting_index} | head -n ${sample_count} | xargs -n1 curl --insecure | gunzip >"${input_dir}/temperatures.full.txt"

# 7/22
# example input:
# 0179066350999992015010100004+47133+007617FM-12+048299999V0202001N001019999999N999999999-01061-01151103901ADDAA101000091AA206000091MA1999999097591MD1510021+9999OD139900211999OD259900101999REMSYN08806635 03/// /2002 11106 21115 39759 40390 55002 60001 333 55300 20000 60005 91104 91202=
# 0162066350999992015010101004+47133+007617FM-12+048299999V0201301N000519999999N999999999-01131-01241103931ADDAA101000091MA1999999097601MD1510001+9999OD139900151999OD259900051999REMSYN08206635 23/// /1301 11113 21124 39760 40393 55000 333 55300 20000 60005 91103 91201=
# 0162066350999992015010102004+47133+007617FM-12+048299999V0201801N001019999999N999999999-01161-01171103981ADDAA101000091MA1999999097641MD1210051+9999OD139900151999OD259900101999REMSYN08206635 23/// /1802 11116 21117 39764 40398 52005 333 55300 20000 60005 91103 91202=
# 0162066350999992015010103004+47133+007617FM-12+048299999V0202401N000519999999N999999999-01141-01241103991ADDAA101000091MA1999999097651MD1210061+9999OD139900151999OD259900101999REMSYN08206635 23/// /2401 11114 21124 39765 40399 52006 333 55300 20000 60005 91103 91202=
# 0162066350999992015010104004+47133+007617FM-12+048299999V0202201N001019999999N999999999-00971-01121103981ADDAA101000091MA1999999097681MD1210081+9999OD139900211999OD259900151999REMSYN08206635 23/// /2202 11097 21112 39768 40398 52008 333 55300 20000 60005 91104 91203=
# 0162066350999992015010105004+47133+007617FM-12+048299999V0200701N000519999999N999999999-01111-01231104051ADDAA101000091MA1999999097721MD1210081+9999OD139900151999OD259900101999REMSYN08206635 23/// /0701 11111 21123 39772 40405 52008 333 55300 20000 60005 91103 91202=
# 0304066350999992015010106004+47133+007617FM-12+048299999V0201601N00051000601CN000300199-01221-01301104091ADDAA101000091AA212000091AA324000091AJ100113100110099AL19900031AY141021AY211021GF109991999999999999999999IA1239KA1240N-01341MA1999999097731MD1210081+9999MW1451REMSYN13606635 01/03 91601 11122 21130 39773 40409 52008 60002 74541 333 21134 3/106 47011 55064 55300 20000 60005 70000 90768 93100 91104 91203=
cat "${input_file}" |
  cut -c 89-92 |
  grep -v 999 |
  awk "{ total += \$1; count++ } END { print total/count }" > ${statistics_dir}/average.txt 


# 7/22
sort ${TEMPDIR}/${input}.types ${TEMPDIR}/${input}.types.rev | uniq -c | awk "\$1 >= 2 {print \$2}"

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
# require whole stream reasoning (paste)
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
# require precise modeling of sed
cat "${1}" | sed "s/T..:..:..//" | cut -d "," -f 1,3 | sort -u | cut -d "," -f 1 | sort | uniq -c | awk "{print \$2,\$1}"


# Source: full_benchmark/pash_benchmark/benchmarks/unix50/scripts/30.sh
# 9.8: TELE-communications
# Exact input:
# Communicate fasT,
# Or you risk being latE...
# The party line's fulL,
# So quick! grab a platE...

# expected output: TELE

# annotation1: directly use the input

# annotation2: relax and use [ and ] in the input
# @assume: "cat ${1}" --> "([a-zA-Z\[\].'!]+\n){4}"

# annotation3:
# @assume: "cat ${1}" --> ".*"
# require whole stream reasoning
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

# expected output: dmr

# annotation1:
# @assume: "cat ${1}" --> "Year\tName\tGender\tCitizenship\tSecond Citizenship\tBorn\tAffiliation at the time of the award\n(([0-9]+{4})\t[a-zA-Z ]+&~(.*Bell.*)\t(Male|Female)\t(.+)&~(.*Bell.*)\t( )*\t([0-9]+{4})\t(.+)&~(.*Bell.*)\n)*(1983	Dennis MacAlistair Ritchie	Male	United States	 	1941	Bell Telephone Laboratories\n)(([0-9]+{4})\t[a-zA-Z ]+\t(Male|Female)\t(.+)\t( )*\t([0-9]+{4})\t(.+)\n)*"

# annotation2:
# @assume: "cat ${1}" --> "Year\tName\tGender\tCitizenship\tSecond Citizenship\tBorn\tAffiliation at the time of the award\n(([0-9]+{4})\t[a-zA-Z ]+\t(Male|Female)\t(.+)\t( )*\t([0-9]+{4})\t(.+)\n)*"

# annotation3:
# @assume: "cat ${1}" --> "Year\tName\tGender\tCitizenship\tSecond Citizenship\tBorn\tAffiliation at the time of the award\n(([0-9]+{4})\t.+\t(Male|Female)\t(.+)\t( )*\t([0-9]+{4})\t(.+)\n)*"

# require whole stream reasoning (especially fmt)
cat ${1} | grep "Bell" | cut -f 2 | head -n 1 | fmt -w1 | cut -c 1-1 | tr -d "\n" | tr "[A-Z]" "[a-z]"

# Github benchmark

# Commit message: Don't forget to escape also the slash "/"
# Commit URL: https://github.com/pi-hole/pi-hole/commit/2061daa902f9dc0f56daccfb024eeaca3ea1398d
# Category: 
# Notes: 
# Changed content:
# - echo $* | sed "s/[]\\.|$(){}?+*^]/\\\\&/g"
# + echo $* | sed "s/[]\\.|$(){}?+*^]/\\\\&/g" | sed "s/\\//\\\\\//g"
################################################################################

# match . \ / | [ ] $ ( ) { } ? + * ^ only if they are escaped (e.g match \. but not ., match \? but not ?)
# require support of references (&)
# stream enable

# annotation 1:
# @assume: "echo $* --> "[^\]\\.|$(){}?+*^/]"
# @output: "[^\]\\.|$(){}?+*^/]"


# annotation 2:
# @assume: "echo $* --> ".*"
# @output: "~(.*[^\\][\].|$(){}?+*^/].*)"
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

# annotation 1:
# @assume: "ip link show" --> "[0-9]+: [a-z0-9.]+@[a-z0-9.]+: <[A-Z, ]+> mtu 1500 qdisc noqueue state UP mode DEFAULT group default qlen 1000 link/ether ([0-9]{2}:){5}[0-9]{2} brd ([0-9a-f]{2}:){5}[0-9a-f]{2}"
# @output "[a-z0-9.]+"
# require precise modeling of sed
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
# require precise modeling of sed
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
# annotation 1:
# assume: "ip -4 addr" --> ".* inet ([0-9]{1,3}\.){3}\.[0-9]{1,3} ([^ \t]+)+ scope global [^ \t]+"
# @output "([0-9]{1,3}\.){3}\.[0-9]{1,3}"


# annotation 2:
# @assume "ip -4 addr" --> ".* inet ([0-9]{1,3}\.){3}\.[0-9]{1,3}( peer ([0-9]{1,3}\.){3}\.[0-9]{1,3})? ([^ \t]+)+ scope global [^ \t]+"
# @output "([0-9]{1,3}\.){3}\.[0-9]{1,3}"
# require precise modeling of sed
# stream enable
	SERVER_PUB_IP=$(ip -4 addr | sed -ne 's|^.* inet \([^/]*\)/.* scope global.*$|\1|p' | awk '{print $1}' | head -1)


################################################################################
# Commit message: fix https://github.com/acmesh-official/acme.sh/issues/3140
# Commit URL: https://github.com/acmesh-official/acme.sh/commit/0c9c1ae673812c14aa4e8ac83831b31961ab9ade
# Category: 
# Notes: 
# Changed content:
# - Le_LinkOrder="$(echo "$responseHeaders" | grep -i '^Location.*$' | _tail_n 1 | tr -d "\r\n" | cut -d ":" -f 2-)"
# + Le_LinkOrder="$(echo "$responseHeaders" | grep -i '^Location.*$' | _tail_n 1 | tr -d "\r\n \t" | cut -d ":" -f 2-)"
################################################################################

# annotation1:
# @assume: "echo "$responseHeaders"" --> \
# "HTTP/2 302\r\n"\
# "content-type: text/html; charset=utf-8\r\n"\
# "location: https://github.com/acmesh-official/acme.sh/releases/tag/v[0-9]+\.[0-9]+\.[0-9]+\r\n"\
# "server: github.com\r\n"
# @assert (whole stream): "https://github.com/acmesh-official/acme.sh/releases/tag/[0-9]+\.[0-9]+\.[0-9]+\n"
# require whole stream reasoning, also related to the \n at the end of the stream
# stream enable
      Le_LinkOrder="$(echo "$responseHeaders" | grep -i '^Location.*$' | _tail_n 1 | tr -d "\r\n" | cut -d ":" -f 2-)"

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
# require whole stream reasoning (grep, awk, tr)
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
# no benifit from the new model
# annotation1:
# @assume: "cat $2" --> "\t*include /etc/nginx/conf\.d/[a-zA-Z0-9_]*\.conf;"
# @output "/etc/nginx/conf\.d/[a-zA-Z0-9_]*\.conf"
cat "${2}" | tr "\t" " " | grep "^ *include *;" | sed "s/include //" | tr -d " ;"


################################################################################
# Commit message: Fix: "\s" is a gawk-specific regexp operator.
# Commit URL: https://github.com/ohmyzsh/ohmyzsh/commit/8b5950b812b56a652ce1101f8d4adc569e516160
# Category: 
# Notes: 
# Changed content:
# - $_comp_command1 --no-ansi | sed "1,/Available commands/d" | awk '/^\s*[a-z]+/ { print $1 }'
# + $_comp_command1 --no-ansi | sed "1,/Available commands/d" | awk '/^[ \t]*[a-z]+/ { print $1 }'
################################################################################
# 7/22
# precise mode
# not sure if this can be caught, but the bug is that "awk" does not support \s character class (only the GNU version, aka "gawk")
# stream enable
# example input:
# Composer 1.10.1 2020-03-13 20:34:27

# Usage:
#   command [options] [arguments]

# Options:
#   -h, --help                     Display this help message
#   -q, --quiet                    Do not output any message
#   -V, --version                  Display this application version
#       --ansi                     Force ANSI output
#       --no-ansi                  Disable ANSI output
#   -n, --no-interaction           Do not ask any interactive question
#       --profile                  Display timing and memory usage information
#       --no-plugins               Whether to disable plugins.
#   -d, --working-dir=WORKING-DIR  If specified, use the given directory as working directory.
#       --no-cache                 Prevent use of the cache
#   -v|vv|vvv, --verbose           Increase the verbosity of messages: 1 for normal output, 2 for more verbose output and 3 for debug

# Available commands:
#   about                Shows the short information about Composer.
#   archive              Creates an archive of this composer package.
#   browse               [home] Opens the package's repository URL or homepage in your browser.
#   check-platform-reqs  Check that platform requirements are satisfied.
#   clear-cache          [clearcache|cc] Clears composer's internal package cache.
#   config               Sets config options.
#   create-project       Creates new project from a package into given directory.
#   depends              [why] Shows which packages cause the given package to be installed.
#   diagnose             Diagnoses the system to identify common errors.
#   dump-autoload        [dumpautoload] Dumps the autoloader.
#   exec                 Executes a vendored binary/script.
#   fund                 Discover how to help fund the maintenance of your dependencies.
#   global               Allows running commands in the global composer dir ($COMPOSER_HOME).
#   help                 Displays help for a command
#   init                 Creates a basic composer.json file in current directory.
#   install              [i] Installs the project dependencies from the composer.lock file if present, or falls back on the composer.json.
#   licenses             Shows information about licenses of dependencies.
#   list                 Lists commands
#   outdated             Shows a list of installed packages that have updates available, including their latest version.
#   prohibits            [why-not] Shows which packages prevent the given package from being installed.
#   remove               Removes a package from the require or require-dev.
#   require              Adds required packages to your composer.json and installs them.
#   run-script           [run] Runs the scripts defined in composer.json.
#   search               Searches for packages.
#   show                 [info] Shows information about packages.
#   status               Shows a list of locally modified packages, for packages installed from source.
#   suggests             Shows package suggestions.
#   update               [u|upgrade] Upgrades your dependencies to the latest version according to composer.json, and updates the composer.lock file.
#   validate             Validates a composer.json and composer.lock.
$_comp_command1 --no-ansi | sed "1,/Available commands/d" | awk '/^[ \t]*[a-z]+/ { print $1 }'





# koala
pr -mts, $file1 $file2 | awk -F',' "{ a[\$2]++; } END { for (n in a) print n \",\" a[n] } " | sort -k2 -n -t',' -r > "$as_popularity"


cat "$input" |
    grep "$city" |
    grep -v "\-99" |
    awk '{ printf "%02d-%02d %s %s\n", $1, $2, $3, $4 }' |
    sort -n >$formatted

cat "$formatted" |
    awk '{
    key = sprintf("%s", $1);
    count[key]++;
    sum[key] += $3;
    sum_sq[key] += $3 * $3;
    if (!(key in max) || $3 > max[key]) max[key] = $3;
    if (!(key in min) || $3 < min[key]) min[key] = $3;
} 
END {
    for (key in max) {
        mean = sum[key] / count[key];
        variance = (sum_sq[key] / count[key]) - (mean * mean);
        stddev = (variance > 0) ? sqrt(variance) : 0;
        confidence_delta = 1.96 * stddev / sqrt(count[key]);
        normal_range_low = mean - confidence_delta;
        normal_range_high = mean + confidence_delta;
        printf "%s %s %s %.2f %.2f\n", key, min[key], max[key], normal_range_low, normal_range_high;
    }
}' | sort -n >"$processed"

awk '($9 ~ /404/)' $tempfile | awk -F\" '($2 ~ "^GET .*.php")' | awk '{print $7}' | sort | uniq -c | sort -r | head -n 20  


# stackoverflow

find . -type f \( -iname "*.xml" \) -printf '%T@ %p\n' |
    sort -rg |
    sed -r 's/[^ ]* //' |
    awk '{w = $0; sub(".*/", "", w); sub("_[0-9_][0-9_]*.*", "", w);} !a[w]++'















