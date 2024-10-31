# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/unix50/scripts/23.sh
# Line: 4

cat $1 | tr ' ' '\n' | grep '[A-Z]' | tr '[a-z]' '\n' | grep '[A-Z]' | tr -d '\n' | cut -c 1-4
