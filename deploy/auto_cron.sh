#!/bin/sh
set -euo pipefail

source /home/webapps/miniconda3/bin/activate auto_qc

cd /export/home/webapps/auto_qc 


echo doing the hiseq 
python manage.py update_database --raw_data_dir /data/archive/hiseq --fastq_data_dir /data/archive/fastq/ --results_dir /data/results/ --config /export/home/webapps/auto_qc/config/config.yaml 

echo doing the miseq 
python manage.py update_database --raw_data_dir /data/archive/miseq --fastq_data_dir /data/archive/fastq/ --results_dir /data/results/ --config /export/home/webapps/auto_qc/config/config.yaml

echo doing the nextseq
python manage.py update_database --raw_data_dir /data/archive/nextseq --fastq_data_dir /data/archive/fastq/ --results_dir /data/results/ --config /export/home/webapps/auto_qc/config/config.yaml 

source /home/webapps/miniconda3/bin/deactivate
