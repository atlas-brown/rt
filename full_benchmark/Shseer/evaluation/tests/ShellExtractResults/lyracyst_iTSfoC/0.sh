#!/bin/bash

lyracyst -o json/define.json wn def $1
lyracyst -o json/example.json wn ex $1
lyracyst -o json/hyphen.json wn hyph $1
lyracyst -o json/origin.json wn ori $1
lyracyst -o json/phrase.json wn phr $1
lyracyst -o json/pronounce.json wn pro $1
lyracyst -o json/relate.json wn rel $1
lyracyst -o json/combine.json rb comb $1
lyracyst -o json/info.json rb inf $1
lyracyst -o json/rhyme.json rb rhy $1
lyracyst -o json/urban.json urb $1
lyracyst -o json/look.json look $1
lyracyst -o json/anagram.json ana $1
