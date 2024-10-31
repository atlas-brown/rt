# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/nlp/scripts/count_vowel_seq.sh
# Line: 12

cat $IN/$input | tr 'a-z' '[A-Z]' | tr -sc 'AEIOU' '[\012*]'| sort | uniq -c  > ${OUT}/${input}.out
