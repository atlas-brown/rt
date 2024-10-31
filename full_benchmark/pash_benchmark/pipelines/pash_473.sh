# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/web-index/p1.sh
# Line: 17

cat $WIKI/input/index.txt | xargs -0 -d '\n' -n 1 bash -c 'page_per_line "$@"'
