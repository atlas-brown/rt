# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/nlp/scripts/trigram_rec.sh
# Line: 24

cat $IN/$input | grep 'And he said' | pure_func ${input} | sort -nr | sed 5q > ${OUT}/${input}.1.out
