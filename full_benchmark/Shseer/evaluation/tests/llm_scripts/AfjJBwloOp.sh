#!/bin/sh

read -p "Enter a prefix math expression: " expression

result=$(echo "scale=2; $expression" | bc)

echo "Result: $result"