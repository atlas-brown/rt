# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/riker/WITH_DOCKER/lsof/lsof_build.sh
# Line: 22

echo '#define LSOF_CCFLAGS "'`echo $CFLAGS | sed 's/\\\\(/\\(/g' | sed 's/\\\\)/\\)/g' | sed 's/"/\\\\"/g'`'"' >> version.h
