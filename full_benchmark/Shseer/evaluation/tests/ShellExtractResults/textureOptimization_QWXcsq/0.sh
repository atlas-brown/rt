#!/bin/bash          

# compile
cmake . && make

# test
ls input/ | xargs -P 4 -I {} ./textureOptimization input/{}


# test
# for input in $(ls input/);
# do
# 	echo $input    
# 	./textureOptimization input/$input
# done