#! /usr/bin/gnuplot
set terminal pngcairo size 640,480 enhanced font 'Arial, 14'
set output 'graph-mean.png'

set title "Execution time + 3-sigma interval (ticks)"
set border linewidth 1.2
set nokey
set grid
#set mytics 0
set style line 1 linecolor rgb 'cyan' linetype 1 linewidth 1
set style line 2 linecolor rgb 'blue' linetype 1 linewidth 1.5
set ylabel 'Execution time (ticks)'
set xlabel 'Run'
set format y "%.0f"
set format x "%.0f"
set xtics font "Arial, 12"
set ytics font "Arial, 12"

#set style fill pattern 2
set style fill solid 0.25 border
#set yrange [12750000:13200000]
plot "mean.dat" using 1:($4+3*$5):($4-3*$5) with filledcurve ls 1,\
     "mean.dat" using 1:($4+3*$5) with lines ls -1,\
     "mean.dat" using 1:($4-3*$5) with lines ls -1,\
     "mean.dat" using 1:4 with points ls 2

#plot "mean.dat" using 1:4 with lines ls 1,\
#     "mean.dat" using 1:($4+3*$5) with lines ls 2,\
#     "mean.dat" using 1:($4-3*$5) with lines ls 2

#plot "mean.dat" using 1:4 with points ls 1,\
#     "mean.dat" using 1:4:5 with yerrorbars ls 2

