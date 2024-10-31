# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/unix50/scripts/20.sh
# Line: 4

cat $1 | grep '(' | cut -d '(' -f 2 | cut -d ')' -f 1 | head -n 1
