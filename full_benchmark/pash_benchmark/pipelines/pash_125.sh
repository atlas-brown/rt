# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/nlp/scripts/letter_words.sh
# Line: 13

cat $IN/$input | tr -c 'A-Za-z' '[\n*]' | grep -v "^\s*$" | grep -c '^....$' > ${OUT}/${input}.out0
