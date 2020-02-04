#!/bin/sh
set -euo pipefail

source /home/webapps/miniconda3/bin/activate auto_qc

cd /export/home/webapps/auto_qc 


echo doing the hiseq 
python manage.py update_database --raw_data_dir /data/archive/hiseq  --config /export/home/webapps/auto_qc/config/config_gen01.yaml 

echo doing the miseq 
python manage.py update_database --raw_data_dir /data/archive/miseq  --config /export/home/webapps/auto_qc/config/config_gen01.yaml 

echo doing the nextseq
python manage.py update_database --raw_data_dir /data/archive/nextseq --config /export/home/webapps/auto_qc/config/config_gen01.yaml 

echo doing the novaseq/dragen
python manage.py update_database --raw_data_dir /data/archive/novaseq/BCL --config /export/home/webapps/auto_qc/config/config_gen01.yaml 

echo doing the nipt
python manage.py load_nipt --raw_data_dir /data/archive/nipt/runs


source /home/webapps/miniconda3/bin/deactivate
