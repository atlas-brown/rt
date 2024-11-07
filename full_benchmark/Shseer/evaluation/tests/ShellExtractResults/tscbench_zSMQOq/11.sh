#! /usr/bin/gnuplot
set terminal pngcairo size 640,480 enhanced font 'Arial, 14'
#set terminal png size 640,480 enhanced font 'Arial, 11'
set output 'graph-overhead-rse.png'
set title "Overhead of TSC reading"
set border linewidth 1.2
set nokey
set grid
#set mytics 0
set style line 1 linecolor rgb 'red' linetype 1 linewidth 1.5
set style line 2 linecolor rgb 'blue' linetype 1 linewidth 1.5
set ylabel 'Overhead (ticks)'
set xlabel 'Run'
set format y "%.1f"
set format x "%.0f"

set xtics font "Arial, 12" 
set ytics font "Arial, 12" 
set yrange [97:100]

plot "overhead-rse.dat" using 1:2 with points ls 1
#     "overhead-root-rse.dat" using 1:2 with points ls 2
