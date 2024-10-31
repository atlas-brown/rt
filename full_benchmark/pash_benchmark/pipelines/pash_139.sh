# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/nlp/scripts/vowel_sequencies_gr_1K.sh
# Line: 12

cat $IN/$input | tr -c 'A-Za-z' '[\n*]' | grep -v "^\s*$" | tr -sc 'AEIOUaeiou' '[\012*]' | sort | uniq -c | awk "\$1 >= 1000" > ${OUT}/${input}.out
