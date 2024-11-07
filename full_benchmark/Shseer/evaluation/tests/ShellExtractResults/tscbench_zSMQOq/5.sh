#! /usr/bin/gnuplot
set terminal pngcairo size 640,480 enhanced font 'Arial, 14'
set output 'graph-mean.png'

set title "Execution time statistic (ticks)"
set border linewidth 1.2
set key top right font "Arial, 12"
set grid
#set mytics 0
set style line 1 linecolor rgb 'green' linetype 1 linewidth 1
set style line 2 linecolor rgb 'blue' linetype 1 linewidth 1.5
set style line 3 linecolor rgb 'cyan' linetype 1 linewidth 1
set style line 4 linecolor rgb 'red' linetype 1 linewidth 1
set ylabel 'Execution time (ticks)'
set xlabel 'Run'
set format y "%.0f"
set format x "%.0f"
set xtics font "Arial, 12"
set ytics font "Arial, 12"

#set style fill pattern 2
set style fill solid 0.25 border
#set yrange [12750000:13200000]
#plot "mean.dat" using 1:($4+3*$5):($4-3*$5) title "3-sigma" with filledcurve ls 1,\
#     "mean.dat" using 1:($4+3*$5) notitle with lines ls -1,\
#     "mean.dat" using 1:($4-3*$5) notitle with lines ls -1,\
#     "mean.dat" using 1:($4+2*$5):($4-2*$5) title "2-sigma" with filledcurve ls 3,\
#     "mean.dat" using 1:($4+2*$5) title "" with lines ls -1,\
#     "mean.dat" using 1:($4-2*$5) title "" with lines ls -1,\
#     "mean.dat" using 1:4 title "mean" with points ls 2,\
#     "mean.dat" using 1:8 title "min" with lines ls 4,\
#     "mean.dat" using 1:9 title "max" with lines ls 4

plot "mean.dat" using 1:4:(3*$5) with yerrorbars ls 1,\
     "mean.dat" using 1:4 with points ls 2

