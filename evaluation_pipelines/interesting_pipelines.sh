#!/bin/bash unix50/16.sh

# 7.2: find  most frequently occurring machine
cat $1 "-->.* .*" | cut -f 2 "-->[0-9]+" | sort -n | uniq -c | sort -nr | head -n 1 | tr -s ' ' '\n' | tail -n 1

cat $1 "-->.* .*" | cut -f 2 | sort -n | uniq -c | sort -nr | head -n 1 | tr -s ' ' '\n' | tail -n 1

cat $1 | cut -f 2 | sort -n | uniq -c | sort -nr | head -n 1 | tr -s ' ' '\n' | tail -n 1



# #!/bin/bash unix50/17.sh

# # 7.3: all the decades in which a unix version was released
# cat $1 | cut -f 4 | sort -n | cut -c 3-3 | uniq | sed s/\$/'0s'/

# # intercode_81_gold2.sh

# df -m /system | grep / | tr -s ' ' | cut -d ' ' -f 4

#     # {
#     #     "message": "fix server host",
#     #     "commit_url": "https://github.com/acmesh-official/acme.sh/commit/98394f99b5649be9df419fd3bed5bfef4658971c",
#     #     "removed_lines": [
#     #         "-  _ACME_SERVER_HOST=\"$(echo \"$ACME_DIRECTORY\" | cut -d : -f 2 | tr -d '/')\""
#     #     ],
#     #     "added_lines": [
#     #         "+  _ACME_SERVER_HOST=\"$(echo \"$ACME_DIRECTORY\" | cut -d : -f 2 | tr -s / | cut -d / -f 2)\""
#     #     ],
#     #     "repo": "acmesh-official/acme.sh",
#     #     "category": "",
#     #     "notes": ""
#     # },

# echo "$ACME_DIRECTORY" | cut -d : -f 2 | tr -s / | cut -d / -f 2

# # full_benchmark/Shseer/evaluation/tests/ShellExtractResults/AUR_BZibXo/4258.sh
# 	# 5)	# hostname and IP (static)
# 	# 	hostname=$(hostname)
# 	# 	dnsname=$(dnsdomainname)
# 	# 	IP=$(ip addr | grep inet | grep eth0 | tr -s ' ' | cut -d' ' -f3 | cut -d'/' -f1)
# 	# 	echo -ne "s\tHostname:\t"${hostname:-<unknown>}"."${dnsname:-<unknown>}"\tIP: "${IP:-N/A}
# 	# 	exit
#     #     	;;

# ip addr | grep inet | grep eth0 | tr -s ' ' | cut -d' ' -f3 | cut -d'/' -f1

# 	# 11)	# video disk usage
# 	# 	VAR=$(df -Pk srv/vdr/video | tail -n 1 | tr -s ' ' | cut -d' ' -f 2,4)
# 	# 	echo -ne "Video Disk:\t"$VAR
# 	# 	exit
#     #     	;;

# df -Pk srv/vdr/video | tail -n 1 | tr -s ' ' | cut -d' ' -f 2,4

# # full_benchmark/Shseer/evaluation/tests/ShellExtractResults/jax_NcIfYu/8.sh
# pip3 list | grep jaxlib | tr -s ' ' | cut -d " " -f 2 | cut -d "+" -f 1

# # full_benchmark/Shseer/evaluation/tests/ShellExtractResults/lnmp_ALrrxd/6.sh
# ps -ef | grep java | grep $CATALINA_HOME/ | grep -v grep | tr -s " "|cut -d" " -f2
