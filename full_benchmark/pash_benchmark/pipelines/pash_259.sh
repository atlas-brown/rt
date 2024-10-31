# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/riker/WITH_DOCKER/vim/vim_build.sh
# Line: 18

echo 'char_u *default_vimruntime_dir = (char_u *)"";' | sed -e 's/[\\"]/\\&/g' -e 's/\\"/"/' -e 's/\\";$/";/' -e 's/  */ /g' >> auto/pathdef.c
