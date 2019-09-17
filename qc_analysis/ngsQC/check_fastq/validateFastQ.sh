#!/bin/bash

for file in /data/archive/fastq/190726_NB551415_0023_AH57WGAFXY-TEST/Data/19M10265/*.gz;
do gunzip -c $file > ${file%.*}; done 

for file in /data/archive/fastq/190726_NB551415_0023_AH57WGAFXY-TEST/Data/19M10265/*.fastq;
do value=$(/home/transfer/fastqValidator/fastQValidator/bin/fastQValidator --file ${file});
if [[ "$value" != *"SUCCESS"* ]]; then
echo "EMAIL-failed by fastqValidator";
else echo "fastq passed by fastqValidator"
fi
 done

rm /data/archive/fastq/190726_NB551415_0023_AH57WGAFXY-TEST/Data/19M10265/*.fastq
