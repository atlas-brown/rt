# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/riker/vim_build.sh
# Line: 21

echo 'char_u *all_lflags = (char_u *)"gcc '$LFLAGS' -o vim '$LIBS'";' | sed -e 's/[\\"]/\\&/g' -e 's/\\"/"/' -e 's/\\";$/";/' -e 's/  */ /g' >>  auto/pathdef.c
