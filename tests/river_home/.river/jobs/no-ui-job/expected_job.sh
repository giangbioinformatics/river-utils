#!/bin/bash
#SBATCH --job-name=uuid
#SBATCH --time=1:00:00
#SBATCH --output=./tests/river_home/.river/jobs/uuid/job.log
#SBATCH --mem=1G
#SBATCH --cpus-per-task=1
source ~/.river.sh

# Boostrap
# No bootstrap script


# Symlink analysis
ln -sf ./tests/river_home/.river/tools/<<analysis>> ./tests/river_home/.river/jobs/uuid/<<analysis>>

# Access job
# Tool does not have set the access

# Cloud storage
trap 'umount $MOUNT_POINT || "S3 bucket is not mounted' EXIT
set -euo pipefail

# Mount using goofys
MOUNT_POINT=./tests/river_home/.river/jobs/uuid/workspace 
goofys --profile bucket_name --file-mode=0700 --dir-mode=0700 --endpoint=endpoint bucket_name $MOUNT_POINT

# Main
sleep 1
echo "Start analysis"
nextflow run ./river-quality-control-ngs \
    -profile singularity \
    --reads "workspace<<fastqs_dir>>*{1,2}.fq" \
    -work-dir "workspace/work" \
    --outdir "workspace<<output_folder>>"