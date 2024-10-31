# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/nlp/scripts/verses_2om_3om_2instances.sh
# Line: 15

cat $IN/$input | grep 'light.\*light' | grep -vc 'light.\*light.\*light' > ${OUT}/${input}.out2
