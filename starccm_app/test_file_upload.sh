#!/bin/bash
#SBATCH -J starccmref
#SBATCH -N 2
#SBATCH -n 

set -o xtrace
set -e

export PATH=$PATH:/opt/STAR-CCM+14.06.012/star/bin
# export PATH=$PATH:/share/apps/cd-adapco/RHEL5/14.06.012/STAR-CCM+14.06.012/star/bin

export OPENMPI_DIR=/opt/openmpi-4.0.4
# export OPENMPI_DIR=/usr/mpi/gcc/openmpi-4.0.3rc4

export PATH=${OPENMPI_DIR}/bin:$PATH
export LD_LIBRARY_PATH=${OPENMPI_DIR}/lib

# Reports on the versions
which ompi_info
which mpirun
ompi_info | grep btl
ompi_info | grep ucx
sleep 5

# Kill any accidental leftovers from previous runs
kill_starccm+

export CDLMD_LICENSE_FILE="27012@Licserv0001.scania.com:27012@Licserv0002.scania.com:27012@Licserv0003.scania.com:28060@caxsrv17p28060.wob.vw.vwg"

SIM_FILE=/tmp/SteadyFlowBackwardFacingStep_final.sim
STAR_CLASS_PATH="/share/apps/poi-3.7-FINAL"
NODE_FILE="nodelist_${SLURM_JOB_ID}"

# Assemble a nodelist
hostListbin=/share/apps/hostlist/python-hostlist-1.18/hostlist
$hostListbin --append=: --append-slurm-tasks=$SLURM_TASKS_PER_NODE -e $SLURM_JOB_NODELIST >  $NODE_FILE


starccm+ -machinefile ${NODE_FILE} \
         -power \
         -batch /tmp/starccmSim.java \
         -np $SLURM_NTASKS \
         -classpath $STAR_CLASS_PATH \
         -fabricverbose \
         -mpi openmpi \
         -mpiflags "--mca pml ucx --mca btl openib --mca pml_base_verbose 10 --mca mtl_base_verbose 10"  \
         $SIM_FILE
 # Kill off any rogue processes
 kill_starccm+