# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/media-conv/verify.sh
# Line: 34

hash_audio_dir "$results_dir/$bench" | diff -q "$hashes_dir/$bench.md5sum" -
