#!/bin/bash
#SBATCH --account=admin
#SBATCH --mail-type=ALL
#SBATCH --job-name=mpitest
#SBATCH --nodes=1
#SBATCH --cores-per-socket=1
#SBATCH --partition=debug
#SBATCH --time=00:15:00
#SBATCH --exclusive
set -o xtrace
set -e
export PATH=$PATH:/usr/mpi/gcc/openmpi-4.0.3rc4/bin
[[ $(mpirun --version | grep 4.0.3) ]] && echo "MPI version OK" || exit 1

if dpkg -l mpitests ; then echo "mpitests installed OK"; fi

NP=2
MPIPROG=/usr/local/libexec/osu-micro-benchmarks/mpi/startup/osu_hello
mpirun -np ${NP} ${MPIPROG}
