#!/bin/bash

for i in $(find hacks -name \*.rb) 
do
  cat $PWD/license.txt $i > ${i}_2
  echo $i
  rm $i
  mv "${i}_2" $i
done
