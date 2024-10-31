# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/covid-mts/input.sh
# Line: 9

curl --insecure 'https://atlas-group.cs.brown.edu/data/covid-mts/in.csv.gz' | gunzip > "$input_dir/in.csv"
