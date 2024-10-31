# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/unix50/scripts/14.sh
# Line: 4

cat $1 | awk "{print \$2, \$0}" | sort -nr | cut -d ' ' -f 2
