# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/riker/vim_build.sh
# Line: 20

echo 'char_u *all_cflags = (char_u *)"'$CFLAGS'";' | sed -e 's/[\\"]/\\&/g' -e 's/\\"/"/' -e 's/\\";$/";/' -e 's/  */ /g' >>  auto/pathdef.c
