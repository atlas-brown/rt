#! /bin/bash

for i in $(seq 1 16);
do
  port=$((8000 + $i))   
  python ../src/webapp.py --port $port& 
done
