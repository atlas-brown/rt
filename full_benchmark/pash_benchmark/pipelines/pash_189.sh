# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/riker/vim_build.sh
# Line: 19

echo 'char_u *default_vimruntime_dir = (char_u *)"";' | sed -e 's/[\\"]/\\&/g' -e 's/\\"/"/' -e 's/\\";$/";/' -e 's/  */ /g' >> auto/pathdef.c
