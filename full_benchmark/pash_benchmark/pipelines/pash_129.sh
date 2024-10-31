# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/nlp/scripts/sort_words_by_rhyming.sh
# Line: 12

cat $IN/$input | tr -c 'A-Za-z' '[\n*]' | grep -v "^\s*$" | sort | uniq -c | rev | sort | rev
