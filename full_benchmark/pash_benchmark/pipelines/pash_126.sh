# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/nlp/scripts/merge_upper.sh
# Line: 13

cat $IN/$input | tr '[a-z]' '[A-Z]' |  tr -c 'A-Za-z' '[\n*]' | grep -v "^\s*$" | sort | uniq -c > ${OUT}/${input}.out
