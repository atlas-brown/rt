# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/log-analysis/scripts/nginx.sh
# Line: 14

awk '($9 ~ /404/)' $tempfile | awk '{print $7}' | sort | uniq -c | sort -rn
