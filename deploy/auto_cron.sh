#!/bin/sh
set -euo pipefail

source /home/autoqc/miniconda3/bin/activate auto_qc

cd /u01/apps/autoqc/auto_qc/


echo -e INFO"\t"$(date +%Y-%m-%d_%H-%M-%S)"\t"doing the wren novaseq
python manage.py update_database --raw_data_dir /mnt/wren/wren_archive/quality_temp/novaseq/ --config /u01/apps/autoqc/auto_qc/config/config_webserver.yaml

echo -e INFO"\t"$(date +%Y-%m-%d_%H-%M-%S)"\t"doing the wren miseq
python manage.py update_database --raw_data_dir /mnt/wren/wren_archive/quality_temp/miseq/ --config /u01/apps/autoqc/auto_qc/config/config_webserver.yaml

echo -e INFO"\t"$(date +%Y-%m-%d_%H-%M-%S)"\t"doing the wren nextseq
python manage.py update_database --raw_data_dir /mnt/wren/wren_archive/quality_temp/nextseq/ --config /u01/apps/autoqc/auto_qc/config/config_webserver.yaml

source /home/autoqc/miniconda3/bin/deactivate
