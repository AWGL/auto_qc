#!/bin/sh
set -euo pipefail

source /home/webapps/miniconda3/bin/activate auto_qc

cd /export/home/webapps/auto_qc 


echo doing the wren novaseq
python manage.py update_database --raw_data_dir /mnt/wren_archive/quality_temp/novaseq/ --config /export/home/webapps/auto_qc/config/config_gen01.yaml

echo doing the wren miseq
python manage.py update_database --raw_data_dir /mnt/wren_archive/quality_temp/miseq/ --config /export/home/webapps/auto_qc/config/config_gen01.yaml

echo doing the wren nextseq
python manage.py update_database --raw_data_dir /mnt/wren_archive/quality_temp/nextseq/ --config /export/home/webapps/auto_qc/config/config_gen01.yaml

source /home/webapps/miniconda3/bin/deactivate
