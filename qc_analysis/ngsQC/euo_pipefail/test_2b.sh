#! /bin/bash
set -euo pipefail

variable="Complete"

grep "INFO" non_existent_file.txt

echo $variable
