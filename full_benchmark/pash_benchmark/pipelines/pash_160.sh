# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/oneliners/scripts/top-n.sh
# Line: 5

cat $1 | tr -c 'A-Za-z' '[\n*]' | grep -v "^\s*$" | tr A-Z a-z | sort | uniq -c | sort -rn | sed 100q
