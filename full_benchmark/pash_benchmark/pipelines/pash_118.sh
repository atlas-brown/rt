# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/nlp/scripts/compare_exodus_genesis.sh
# Line: 24

cat $IN/$input | tr -c 'A-Za-z' '[\n*]' | grep -v "^\s*$" | sort -u | pure_func $input $INPUT2 > ${OUT}/${input}.out
