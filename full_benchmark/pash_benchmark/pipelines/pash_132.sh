# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/nlp/scripts/syllable_words_2.sh
# Line: 12

cat $IN/$input  | tr -c 'A-Za-z' '[\n*]' | grep -v "^\s*$" | grep -i '^[^aeiou]*[aeiou][^aeiou]*[aeiou][^aeiou]$' | sort | uniq -c | sed 5q > ${OUT}${input}.out
