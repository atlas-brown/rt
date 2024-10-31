# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/log-analysis/scripts/nginx.sh
# Line: 10

tee $tempfile | cut -d "\"" -f3 | cut -d ' ' -f2 | sort | uniq -c | sort -rn
