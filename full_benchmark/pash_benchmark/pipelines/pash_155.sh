# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/oneliners/scripts/nfa-regex.sh
# Line: 4

cat $1 | tr A-Z a-z | grep '\(.\).*\1\(.\).*\2\(.\).*\3\(.\).*\4'
