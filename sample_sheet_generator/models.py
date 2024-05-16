from django.db import models

class Assay(models.Model):

    assay = models.CharField(primary_key=True, max_length=10)
    lims_test = models.CharField(max_length=50, unique=True)
    pipeline_description = models.CharField(max_length=200)
    multiple_sequencers = models.BooleanField(default=False)
