# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/web-index/input/generte_index.sh
# Line: 21

find "$directory_path" -type f | sed 's|./wikipedia/en/articles/||' | sort > index.txt
