# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/nlp/scripts/uppercase_by_token.sh
# Line: 12

cat $IN/$input |  tr -c 'A-Za-z' '[\n*]' | grep -v "^\s*$" | grep -c '^[A-Z]' > ${OUT}/${input}.out
