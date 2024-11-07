#!/bin/bash
#
# nodes - the number of computer nodes in the job
# ppn   - the number of MPI processes per node (ppn!)
# the total number of processes is nodes*ppn
#
#PBS -l nodes=2:ppn=16,walltime=00:15:00
#PBS -N mmmpi
#PBS -q short

cd $PBS_O_WORKDIR

echo MPI
mpirun -np 32 ./mmmpi 5000
echo mkl
./mm 2000 mkl
echo omp
./mm 2000 omp
echo plain
./mm 2000 plain


