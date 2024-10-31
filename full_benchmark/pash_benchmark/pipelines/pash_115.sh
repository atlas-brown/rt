# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/nlp/scripts/bigrams.sh
# Line: 23

cat $IN/$input |  tr -c 'A-Za-z' '[\n*]' | grep -v "^\s*$"| pure_func $input| sort | uniq -c > ${OUT}/${input}.input.bigrams.out
