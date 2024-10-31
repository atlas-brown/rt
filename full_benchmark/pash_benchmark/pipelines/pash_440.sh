# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/unix50/scripts/12.sh
# Line: 4

cat $1 | tr ' ' '\n' | grep '\.' | cut -d '.' -f 2 | cut -c 1-1 | tr '[a-z]' 'P' | sort -r | uniq | head -n 3 | tail -n 1
