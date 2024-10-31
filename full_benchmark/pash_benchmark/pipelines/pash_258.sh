# Source: /home/infinite/Workspace/Brown/Systems transforming systems/stream/full_benchmark/pash_benchmark/benchmarks/riker/WITH_DOCKER/vim/vim_build.sh
# Line: 17

echo 'char_u *default_vim_dir = (char_u *)"/usr/local/share/vim";' | sed -e 's/[\\"]/\\&/g' -e 's/\\"/"/' -e 's/\\";$/";/' -e 's/  */ /g' >> auto/pathdef.c
