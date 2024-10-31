# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/unix50/scripts/4.sh
# Line: 4

cat $1 | cut -d ' ' -f 1 | sort | uniq -c | sort -r
