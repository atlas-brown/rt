# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/teraseq/5TERA-short/run.sh
# Line: 71

zcat "$sdir"/fastq/reads.1.sanitize.wo_rel5.fastq.gz | paste - - - - | cut -f1 | sed 's/^@//g'
