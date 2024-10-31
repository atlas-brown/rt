# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/nlp/scripts/count_consonant_seq.sh
# Line: 12

cat $IN/$input | tr '[a-z]' '[A-Z]' | tr -sc 'BCDFGHJKLMNPQRSTVWXYZ' '[\012*]' | sort | uniq -c > ${OUT}/${input}.out
