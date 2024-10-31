# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/log-analysis/scripts/nginx.sh
# Line: 18

awk -F\" '($2 ~ "/wp-admin/install.php"){print $1}' $tempfile | awk '{print $1}' | sort | uniq -c | sort -r
