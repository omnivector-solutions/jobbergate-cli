#!/bin/sh
############### User defined variables #################
# Slurm output file location
#SBATCH -o ./slurm-%j.out
# Job name
#SBATCH -J Star-CCM+
# An email is sent at state change and at 80% of given time
#SBATCH --mail-type=ALL,TIME_LIMIT_80
# Wait until following jobs have finished
##SBATCH --dependency=afterany:
# Wall-clock time: SLURM timeout [hh:mm:ss]
#SBATCH -t 1:00:00
# Number of MPI processes
#SBATCH -n 20

# Memory requirement
#SBATCH --mem=20G

# Name of account (not user) for accounting.
#SBATCH -A starccm
# Exclusive by default
#SBATCH --exclusive


# Load STAR-CCM+ module
#. /etc/profile.d/z00_lmod.sh # TODO remove when modules are available by default on nodes
#module use /grp/techsim/fluidsim/software/Modules/modulefiles # TODO remove when modules are available by default on nodes
#module add 
# what is inside the directory
#
# /cluster/sesonas13/jbemfv/modules/startestmodules/data.modules
module use /cluster/sesonas13/jbemfv/modules/testmodules/starccm_modules
# Name of sim-file so start simulation from
SIM_FILE=".//cluster/sesonas13/sssler/startests/SteadyFlowBackwardFacingStep_final.sim"
# /cluster/sesonas13/sssler/startests/SteadyFlowBackwardFacingStep_final.sim
# Name of java macro to execute on given sim-file
STARTMACRO="./starccmMesh.java"
# Path to macro library
#STAR_CLASS_PATH="/grp/techsim/fluidsim/software/Java/poi-3.7-FINAL"
STAR_CLASS_PATH=/share/apps/poi-3.7-FINAL
# Name of log file
LOGFILE=starccmMesh.${SLURM_JOBID}.log
############### End of User defined variables #################
# Define license server
export CDLMD_LICENSE_FILE=27012@Licserv0001.scania.com:27012@Licserv0002.scania.com:27012@Licserv0003.scania.com:28060@caxsrv17p28060.wob.vw.vwg


# Copy files to /cluster/...
START_DIR=$SLURM_SUBMIT_DIR
STAGE_DIR="/cluster/sesonas13/$USER/${SLURM_JOB_NAME}_$SLURM_JOBID"
echo "Staging files in $STAGE_DIR"
mkdir -p $STAGE_DIR
cp $SIM_FILE $STAGE_DIR
cp $STARTMACRO $STAGE_DIR
cd $STAGE_DIR
# Save node list to file
export NODEFILE=nodelist_$SLURM_JOB_NAME # Is the export needed?
# /share/apps/hostlist/python-hostlist-1.18/hostlist
/grp/techsim/fluidsim/software/hostlist/python-hostlist-1.18/hostlist --append=: --append-slurm-tasks=$SLURM_TASKS_PER_NODE -e $SLURM_JOB_NODELIST > $NODEFILE
#-batch [mesh|run|step|Java macro file]: no UI
#-np # : amount of processess (/co-simulation instances?)
#-power : use power license
#EXTRA_FLAGS=""
starccm -machinefile $NODEFILE -power -np $SLURM_NTASKS -batch $STARTMACRO -classpath $STAR_CLASS_PATH $SIM_FILE &>> $LOGFILE
# Copy everything back, don't force it
echo "Returning files to $START_DIR"
cp * $START_DIR --no-clobber
cd $START_DIR
# Clean up
rm -r $STAGE_DIR

# License check command:
# scontrol show license

# To replicate this:
# jobberapp.starccm