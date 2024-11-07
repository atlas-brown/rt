#!/bin/bash
ocaml quine.ml | cmp quine.ml
