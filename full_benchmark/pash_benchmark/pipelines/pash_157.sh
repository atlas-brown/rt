# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/oneliners/scripts/shortest-scripts.sh
# Line: 9

cat $1 | xargs file | grep "shell script" | cut -d: -f1 | xargs -L 1 wc -l | grep -v '^0$' | sort -n | head -15
