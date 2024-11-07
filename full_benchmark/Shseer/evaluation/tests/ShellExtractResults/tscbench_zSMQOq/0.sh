#! /usr/bin/gnuplot
set terminal pngcairo size 640,480 enhanced font 'Arial, 14'
set output 'graph-mean.png'

set title "Execution time + 3-sigma interval (ticks)"
set border linewidth 1.2
set nokey
set grid
#set mytics 0
set style line 1 linecolor rgb 'red' linetype 1 linewidth 1.5
set style line 2 linecolor rgb 'green' linetype 1 linewidth 1.5
set style line 3 linecolor rgb 'blue' linetype 1 linewidth 1.5
set style line 4 linecolor rgb 'cyan' linetype 1 linewidth 1.5
set style line 5 linecolor rgb 'orange' linetype 1 linewidth 1.5
set ylabel 'Execution time (ticks)'
set xlabel 'Run'
set format y "%.0f"
set format x "%.0f"
set xtics font "Arial, 12"
set ytics font "Arial, 12"

#set style fill pattern 2
set style fill solid 0.25 border

plot "mean-saxpy-std.dat" using 1:4 with points ls 1,\
     "mean-saxpy-intel.dat" using 1:4 with points ls 2,\
     "mean-saxpy-lfence.dat" using 1:4 with points ls 3,\
     "mean-saxpy-mfence.dat" using 1:4 with points ls 4,\
     "mean-saxpy-cpuid4.dat" using 1:4 with points ls 5
