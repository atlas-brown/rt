#!/usr/bin/env bash
seq 1 100 | tr -d [:alnum:] | sort | uniq | tr [:space:] '\n' | sort | uniq -c | sort -nr | cut -d' ' -f1 | wc -l
