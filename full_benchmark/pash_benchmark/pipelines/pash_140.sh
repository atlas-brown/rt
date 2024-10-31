# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/nlp/scripts/words_no_vowels.sh
# Line: 12

cat $IN/$input | tr -c 'A-Za-z' '[\n*]' | grep -v "^\s*$" | grep -vi '[aeiou]' | sort | uniq -c > ${OUT}/${input}.out
