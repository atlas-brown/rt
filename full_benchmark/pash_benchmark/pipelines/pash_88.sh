# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/log-analysis/scripts/nginx.sh
# Line: 25

awk -F\" '($2 ~ "ref"){print $2}' $tempfile | awk '{print $2}' | sort | uniq -c | sort -r
