#!/bin/bash
gcc quine.c -o quine && ./quine | cmp quine.c && rm quine
