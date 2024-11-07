#!/bin/bash

count=10000
file="$1"

if [[ ! -f "$1" ]]
then
	echo "Usage: $0 filename"
	exit 1
fi

HASH='adler32 crc32 fnv hash md5 random none murmur'

function gather_data {
	for name in $HASH
	do
		python main.py -f "$file" -k $name -l $count --csv-histogram=${name}.csv
	done

	for name in $HASH
	do
		python main.py -f "$file" -k $name -t earlyrotate -l $count --csv-histogram=${name}-earlyrotate.csv
	done

	for name in $HASH
	do
		python main.py -f "$file" -k $name -t earlyrotate2 -l $count --csv-histogram=${name}-earlyrotate2.csv
	done

	python main.py -f "$file" -k none -t avl -l $count --csv-histogram=avl.csv
}

function make_plots {
gnuplot << EOF
set terminal png medium size 800,600

set title  'Node depths histogram - BST'
set ylabel 'frequency'
set xlabel 'depth'
set output 'histogram.png'
set xrange [0:80]
set yrange [0:2000]

plot 'adler32.csv'  title 'Adler32'       with lines,\
     'crc32.csv'    title 'CRC32'         with lines,\
     'fnv.csv'      title 'FNV32'         with lines,\
     'murmur.csv'   title 'Murmur32'      with lines,\
     'hash.csv'     title 'Python hash'   with lines,\
     'md5.csv'      title 'MD5'           with lines,\
     'random.csv'   title 'Pseudo random' with lines,\
     'none.csv'     title 'N/A'           with lines,
EOF


gnuplot << EOF
set terminal png medium size 800,600

set title  'Node depths histogram - BST using "early rotate"'
set ylabel 'frequency'
set xlabel 'depth'
set output 'histogram_early_rotate.png'
set xrange [0:80]
set yrange [0:2000]

plot 'adler32-earlyrotate.csv'  title 'Adler32'       with lines,\
     'crc32-earlyrotate.csv'    title 'CRC32'         with lines,\
     'fnv-earlyrotate.csv'      title 'FNV32'         with lines,\
     'murmur-earlyrotate.csv'   title 'Murmur32'      with lines,\
     'hash-earlyrotate.csv'     title 'Python hash'   with lines,\
     'md5-earlyrotate.csv'      title 'MD5'           with lines,\
     'random-earlyrotate.csv'   title 'Pseudo random' with lines,\
     'none-earlyrotate.csv'     title 'N/A'           with lines,
EOF

gnuplot << EOF
set terminal png medium size 800,600

set title  'Node depths histogram - BST using two "early rotate" methods'
set ylabel 'frequency'
set xlabel 'depth'
set output 'histogram_early_rotate2.png'
set xrange [0:80]
set yrange [0:2000]

plot 'adler32-earlyrotate2.csv'  title 'Adler32'       with lines,\
     'crc32-earlyrotate2.csv'    title 'CRC32'         with lines,\
     'fnv-earlyrotate2.csv'      title 'FNV32'         with lines,\
     'murmur-earlyrotate2.csv'   title 'Murmur32'      with lines,\
     'hash-earlyrotate2.csv'     title 'Python hash'   with lines,\
     'md5-earlyrotate2.csv'      title 'MD5'           with lines,\
     'random-earlyrotate2.csv'   title 'Pseudo random' with lines,\
     'none-earlyrotate2.csv'     title 'N/A'           with lines,
EOF

gnuplot << EOF
set terminal png medium size 800,600

set title  'Node depths histogram - comparision with AVL'
set ylabel 'frequency'
set xlabel 'depth'
set output 'histogram_avl.png'

plot 'fnv.csv'          	title 'FNV32'                     with lines,\
     'fnv-earlyrotate.csv'  title 'FNV32 - early rotate (1)'  with lines,\
     'fnv-earlyrotate2.csv' title 'FNV32 - early rotate (2)'  with lines,\
     'none.csv'         	title 'N/A'                       with lines,\
     'avl.csv'          	title 'AVL'                       with lines
EOF
}

gather_data
make_plots
