# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/nlp/scripts/count_morphs.sh
# Line: 12

cat $IN/$input | sed 's/ly$/-ly/g' | sed 's/ .*//g' | sort | uniq -c > ${OUT}/${input}.out
