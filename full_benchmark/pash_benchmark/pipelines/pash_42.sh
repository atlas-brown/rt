# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/bio/bio1/trim_primers.sh
# Line: 5

find . -maxdepth 1 -name "*.fastq" | xargs -I {}  cutadapt -a TCCTCCGCTTATTGATAGC -o ${OUTPUT}/{}\_trimmed.fastq {};
