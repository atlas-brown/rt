# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/teraseq/5TERA-short/run.sh
# Line: 69

zcat "$sdir"/fastq/reads.1.sanitize.w_rel5.fastq.gz | paste - - - - | cut -f1 | sed 's/^@//g'
