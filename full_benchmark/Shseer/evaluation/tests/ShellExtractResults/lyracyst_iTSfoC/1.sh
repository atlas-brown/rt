#!/bin/bash

lyracyst -o xml/define.xml wn def $1
lyracyst -o xml/example.xml wn ex $1
lyracyst -o xml/hyphen.xml wn hyph $1
lyracyst -o xml/origin.xml wn ori $1
lyracyst -o xml/phrase.xml wn phr $1
lyracyst -o xml/pronounce.xml wn pro $1
lyracyst -o xml/relate.xml wn rel $1
lyracyst -o xml/combine.xml rb comb $1
lyracyst -o xml/info.xml rb inf $1
lyracyst -o xml/rhyme.xml rb rhy $1
lyracyst -o xml/urban.xml urb $1
lyracyst -o xml/look.xml look $1
lyracyst -o xml/anagram.xml ana $1
