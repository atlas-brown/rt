# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/bio/bio1/convert_to_fast.sh
# Line: 6

find . -maxdepth 1 -name "*.fastq" | xargs -I {} cutadapt -o ${OUTPUT}/{}.fasta.gz {}
