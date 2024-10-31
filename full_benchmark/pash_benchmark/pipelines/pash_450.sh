# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/unix50/scripts/21.sh
# Line: 4

cat $1 | tr -c "[a-z][A-Z]" '\n' | sort | awk "length >= 16"
