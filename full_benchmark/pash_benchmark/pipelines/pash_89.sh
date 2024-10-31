# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/log-analysis/scripts/pcaps.sh
# Line: 9

tcpdump -nn -r $tempfile -A 'port 53' 2> /dev/null | sort | uniq |grep -Ev '(com|net|org|gov|mil|arpa)' 2> /dev/null
