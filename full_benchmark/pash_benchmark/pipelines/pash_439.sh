# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/unix50/scripts/11.sh
# Line: 4

cat $1 | tr ' ' '\n' | grep 'x' | grep '\.' | cut -d '.' -f 2 | cut -c 1-1 | tr '[a-z]' 'P' | sort | uniq -c | sort -nr
