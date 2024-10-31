# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/log-analysis/scripts/nginx.sh
# Line: 23

awk -F\" '{print $2}' $tempfile  | awk '{print $2}' | sort | uniq -c | sort -r
