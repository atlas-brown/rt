#!/bin/bash

# wget -O eurofxref-hist.xml https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.xml

gcc -o rn rn.c -lm
gcc -o ma ma.c
gcc -o naivepredict naivepredict.c
gcc -o R2 R2.c

cat eurofxref-hist.xml | \
	sed 's/>/>\n/g' | \
	grep '"USD" rate' | \
	sed 's/.*rate="//;s/"\/>//' | \
	tac | \
	./rn | \
	./ma 10 | \
	./naivepredict | \
	./R2 30 | \
	sort -rn > R2.data


