# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/bio/bio-align/bio.sh
# Line: 33

bwa sampe ./hg19.fasta <(bwa aln -t 4 ./hg19.fasta ./s1_1.fastq) <(bwa aln -t 4 ./hg19.fasta ./s1_2.fastq) ./s1_1.fastq ./s1_2.fastq | samtools view -Shb /dev/stdin > s1.bam
