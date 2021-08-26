# Automatic NGS Pipeline Monitoring and Quality Control

## Introduction

A software system to monitor the status of in house pipeline at AWGS and view and approve quality control data from NGS pipelines.

## Project Workflow

The software consists of several modules and configuration files:

1) Pipelines (pipelines/). This module consists of different classes which each represent a different pipeline run at AWMGL. These classes have methods for detecting whether a pipeline has completed ina valid manner and for collecting relevant QC metrics. The module also contains parsers.py which contains functions for parsing common QC files used in NGS. These classes can be configured for example changing the expected files each pipeline produces using the confi/config.yaml files.
2) config/*.yaml. Specific pipeline configuration. Each pipeline gets a key in the config. The key is a concatanation of the pipeline name, pipeline version and panel. For example GermlineEnrichment-2.5.3-IlluminaTruSightCancer. This way multiple pipelines can use the same class in the pipelines module.
3) update_database.py. Script for updating the database.


## Install

Works on Linux/Mac OS

The software is a Django application using Python 3. It is recommended that the software be deployed in a conda virtual environment.

First install Conda/Miniconda from [1]. Then type the following commands in your terminal to install and setup the application.

```
git clone https://github.com/AWGL/auto_qc.git

cd auto_qc

conda env create -f env/main.yaml

source activate auto_qc

python manage.py migrate

python manage.py makemigrations qc_database

python manage.py migrate
```

## Configure

There are several files which need to be configured to get the application to run:

1) mysite/settings.py - Update the variable CONFIG_PATH to point to the config yaml below.

2) mysite/settings.py - Uncomment the first DATABASES variable surronded by """ """, and comment out the second DATABASES variable.

3) config/config.yaml - Pipeline specific variables - see example for how to set this up.

## Update

To update the database the following script will need to be run:

raw_data_dir = raw data from sequencer e.g. bcl, Interop, SampleSheet.csv etc

fastq_data_dir = directory with fastqs

results_dir = directory with pipeline output

config = YAML config file specifiying pipeline specific variables
```
python manage.py update_database --raw_data_dir /media/joseph/Storage/data/archive/nextseq \
								--config config/config_local.yaml

```

It is recommended you set up a cronjob to automate the update of the database.


## Test

```
python manage.py test
```

## Run Webapp

```
python manage.py runserver
```

## FAQ

## References

[1] https://conda.io/miniconda.html

