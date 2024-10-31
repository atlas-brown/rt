# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/log-analysis/scripts/nginx.sh
# Line: 16

awk '($9 ~ /502/)' $tempfile | awk '{print $7}' | sort | uniq -c | sort -r
