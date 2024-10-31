# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/riker/sqlite_build.sh
# Line: 15

cat parse.h ./src/vdbe.c | tclsh8.6 ./tool/mkopcodeh.tcl >opcodes.h
