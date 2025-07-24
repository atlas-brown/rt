# sed
# Intercode
echo "http://www.google.com" | sed -E 's|https?://([^/]+).*|\1|'


# Source: full_benchmark/koala/covid/scripts/5.sh
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

# Source: full_benchmark/pash_benchmark/benchmarks/max-temp/input.sh
seq ${FROM} ${TO} | sed "s;^;${URL};" | sed "s;$;/;" | xargs -n1 -r curl --insecure | grep gz | sed "s;.*\"\\(.*\\)\\(20[0-9][0-9]\\).gz\".*;${URL}\2/\1\2.gz;" | tail -n +${sample_starting_index} | head -n ${sample_count} | xargs -n1 curl --insecure | gunzip >"${input_dir}/temperatures.full.txt"

# Source: full_benchmark/koala/covid/scripts/1.sh
cat "$1" |                    # assumes saved input
  sed 's/T..:..:..//' |     # hide times
  cut -d ',' -f 1,3 |       # keep only day and bus no
  sort -u |                 # remove duplicate records due to time
  cut -d ',' -f 1 |         # keep all dates
  sort |                    # preparing for uniq
  uniq -c |                 # count unique dates
  awk "{print \$2,\$1}"     # print first date, then count

# Source: full_benchmark/pash_benchmark/benchmarks/unix50/scripts/30.sh
cat ${1} | tr -c "[a-z][A-Z]" "\n" | grep "[A-Z]" | sed 1d | sed 2d | sed 3d | sed 4d | tr -c "[A-Z]" "\n" | tr -d "\n"

# Github
# Source: https://github.com/pi-hole/pi-hole/commit/2061daa902f9dc0f56daccfb024eeaca3ea1398d
echo $* | sed "s/[]\\.|$(){}?+*^]/\\\\&/g" | sed "s/\\//\\\\\//g"

# Source: https://github.com/pi-hole/pi-hole/commit/5cebceadda93ceb73038b6d248044933af2e0459
interfaces="$(ip link show | sed "/ master /d;/UP/!d;s/^[0-9]*: //g;s/@.*//g;s/: <.*//g;")"

# Source: https://github.com/ohmyzsh/ohmyzsh/commit/c56fa996e7cb1500dca97723d525e4c97af33c75
rake --silent --tasks | cut -d " " -f 2 | sed 's/\[.*\]//g' > .rake_tasks

# Source: https://github.com/angristan/wireguard-install/commit/e05e633014628a65942cffab66f68228b6e17f7a
SERVER_PUB_IP=$(ip -4 addr | sed -ne 's|^.* inet \([^/]*\)/.* scope global.*$|\1|p' | awk '{print $1}' | head -1)



# awk

# Source: full_benchmark/koala/weather/scripts/temp-analytics.sh
cat "${input_file}" |
  cut -c 89-92 |
  grep -v 999 |
  awk "{ total += \$1; count++ } END { print total/count }" > ${statistics_dir}/average.txt 

# Source: full_benchmark/koala/nlp/scripts/find_anagrams.sh
sort ${TEMPDIR}/${input}.types ${TEMPDIR}/${input}.types.rev | uniq -c | awk "\$1 >= 2 {print \$2}"

# Source: full_benchmark/koala/analytics/scripts/port-scan.sh
pr -mts, $file1 $file2 | awk -F',' "{ a[\$2]++; } END { for (n in a) print n \",\" a[n] } " | sort -k2 -n -t',' -r > "$as_popularity"

# Source: full_benchmark/koala/weather/scripts/tuft-weather.sh
cat "$input" |
    grep "$city" |
    grep -v "\-99" |
    awk '{ printf "%02d-%02d %s %s\n", $1, $2, $3, $4 }' |
    sort -n >$formatted

# Source: full_benchmark/koala/weather/scripts/tuft-weather.sh
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

# Source: full_benchmark/koala/analytics/scripts/nginx.sh
awk '($9 ~ /404/)' $tempfile | awk -F\" '($2 ~ "^GET .*.php")' | awk '{print $7}' | sort | uniq -c | sort -r | head -n 20  

# Source: https://github.com/ohmyzsh/ohmyzsh/commit/8b5950b812b56a652ce1101f8d4adc569e516160
$_comp_command1 --no-ansi | sed "1,/Available commands/d" | awk '/^[ \t]*[a-z]+/ { print $1 }'

# Stackoverflow
find . -type f \( -iname "*.xml" \) -printf '%T@ %p\n' |
    sort -rg |
    sed -r 's/[^ ]* //' |
    awk '{w = $0; sub(".*/", "", w); sub("_[0-9_][0-9_]*.*", "", w);} !a[w]++'


# paste
# Source: full_benchmark/pash_benchmark/benchmarks/teraseq/dRNASeq/run_dRNASeq.sh
zcat $sdir/fastq/reads.1.sanitize.w_rel5.fastq.gz | paste - - - - | cut -f1 | sed 's/^@//g'


# fmt

# Source: full_benchmark/pash_benchmark/benchmarks/unix50/scripts/34.sh
cat ${1} | grep "Bell" | cut -f 2 | head -n 1 | fmt -w1 | cut -c 1-1 | tr -d "\n" | tr "[A-Z]" "[a-z]"


# tr
# Source: https://github.com/acmesh-official/acme.sh/commit/0c9c1ae673812c14aa4e8ac83831b31961ab9ade
Le_LinkOrder="$(echo "$responseHeaders" | grep -i '^Location.*$' | _tail_n 1 | tr -d "\r\n" | cut -d ":" -f 2-)"

# Source: https://github.com/pi-hole/pi-hole/commit/523f6501576f76bfcc7e5d3ddc3cf0a287089790
curl -sI https://github.com/pi-hole/FTL/releases/latest | grep --color=never -i Location | awk -F / '{print $NF}' | tr -d '[:cntrl:]'