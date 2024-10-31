# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/teraseq/5TERA-short/run.sh
# Line: 108

samtools view -@ $threads -bh "$sdir"/align/reads.1.sanitize.toRibosomal.sorted.sam | samtools sort -@ $threads -
