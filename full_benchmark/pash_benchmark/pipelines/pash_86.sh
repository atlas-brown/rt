# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/log-analysis/scripts/nginx.sh
# Line: 20

awk '($9 ~ /404/)' $tempfile | awk -F\" '($2 ~ "^GET .*.php")' | awk '{print $7}' | sort | uniq -c | sort -r | head -n 20
