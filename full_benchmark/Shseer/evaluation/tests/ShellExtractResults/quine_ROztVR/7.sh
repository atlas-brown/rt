#!/bin/bash
exit_code=0
test_script="./test.sh"
for dir in *; do
  if [ -d $dir ]; then
    cd $dir
    bash $test_script
    if [ $? -ne 0 ]; then
      exit_code=1
    fi
    cd ..
  fi
done
exit $exit_code
