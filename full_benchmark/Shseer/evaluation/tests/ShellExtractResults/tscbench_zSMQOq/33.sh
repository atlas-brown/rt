#! /usr/bin/gnuplot
set terminal pngcairo size 640,480 enhanced font 'Arial, 14'
#set terminal png size 640,480 enhanced font 'Arial, 11'
set output 'graph-overhead.png'
set title "Overhead of TSC reading"
set border linewidth 1.2
set key top right
set grid
#set mytics 0
set style line 1 linecolor rgb 'red' linetype 1 linewidth 1.5
set style line 2 linecolor rgb 'blue' linetype 1 linewidth 1.5
set style line 3 linecolor rgb 'green' linetype 1 linewidth 1.5
set style line 4 linecolor rgb 'cyan' linetype 1 linewidth 1.5
set style line 5 linecolor rgb 'orange' linetype 1 linewidth 1.5
set ylabel 'Overhead (ticks)'
set xlabel 'Run'
set format y "%.0f"
set format x "%.0f"

set xtics font "Arial, 12" 
set ytics font "Arial, 12" 

plot "overhead-std.dat" using 1:2 title "Std" with points ls 1 pt 2,\
     "overhead-intel.dat" using 1:2 title "Intel-howto" with points ls 2,\
     "overhead-lfence.dat" using 1:2 title "Std-lfence" with points ls 3,\
     "overhead-mfence.dat" using 1:2 title "Std-mfence" with points ls 4,\
     "overhead-cpuid4.dat" using 1:2 title "Four-cpuid" with points ls 5