# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/unix50/scripts/17.sh
# Line: 4

cat $1 | cut -f 4 | sort -n | cut -c 3-3 | uniq | sed s/\$/'0s'/
