# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/nlp/scripts/sort_words_by_num_of_syllables.sh
# Line: 21

cat $IN/$input | tr -c 'A-Za-z' '[\n*]' | grep -v "^\s*$" | sort -u | pure_func $input > ${OUT}/${input}.out
