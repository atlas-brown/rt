# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/unix50/scripts/32.sh
# Line: 4

cat $1 | sed 1d | grep 'Bell' | cut -f 2 | wc -l
