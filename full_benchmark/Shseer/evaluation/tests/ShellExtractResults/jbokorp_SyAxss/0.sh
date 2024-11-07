#!/bin/bash

wget https://svn.spraakdata.gu.se/repos/lb/trunk/sbkhs/pub/corpus_import.zip
unzip corpus_import.zip
cp corpus_import/corpora/Makefile.common corpus_import/
cp corpus_import/corpora/Makefile.rules corpus_import/
