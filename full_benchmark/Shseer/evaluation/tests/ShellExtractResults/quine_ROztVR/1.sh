#!/bin/bash
javac quine.java && java quine | cmp quine.java && rm quine.class
