# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/unix50/scripts/34.sh
# Line: 4

cat $1 | grep 'Bell' | cut -f 2 | head -n 1 | fmt -w1 | cut -c 1-1 | tr -d '\n' | tr '[A-Z]' '[a-z]'
