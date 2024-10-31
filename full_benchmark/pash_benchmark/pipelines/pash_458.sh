# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/unix50/scripts/29.sh
# Line: 4

cat $1 | sed 2d | sed 2d | tr -c '[A-Z]' '\n' | tr -d '\n'
