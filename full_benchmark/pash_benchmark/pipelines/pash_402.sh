# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/teraseq/RiboSeq/hash_result.sh
# Line: 20

sqlite3 "$g" "SELECT * FROM genome transcr" | sha256sum
