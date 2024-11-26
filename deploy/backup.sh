
# for details on backup and restore - see https://www.postgresql.org/docs/9.1/backup-dump.html#BACKUP-DUMP-RESTORE

BACKUP_DIR="/u02/backups/auto_qc/"

# Backup Postgres DB
/usr/bin/pg_dump auto_qc -U auto_qc_user -h localhost | gzip >  "$BACKUP_DIR"/"$(date '+%Y%m%d%H%M%S')_auto_qc.txt.gz"


