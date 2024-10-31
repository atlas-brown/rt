# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/riker/WITH_DOCKER/lsof/lsof_build.sh
# Line: 20

echo '#define LSOF_CCV "'`cc -v 2>&1 | sed -n 's/.*version \(.*\)/\1/p'`'"' >> version.h
