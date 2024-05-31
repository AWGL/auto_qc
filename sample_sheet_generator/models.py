from django.db import models

class Assay(models.Model):

    INDEX_CHOICES = (
        ("1", "Single Index"),
        ("2", "Dual Index"),
        ("T", "TSO")
    )

    SAMPLE_WELL_CHOICES = (
        ("P", "Position"),
        ("I", "Index Well")
    )

    assay = models.CharField(primary_key=True, max_length=10)
    lims_test = models.CharField(max_length=50, unique=True)
    pipeline_description = models.CharField(max_length=200)
    multiple_sequencers = models.BooleanField(default=False)
    index_fields = models.CharField(max_length=1, choices=INDEX_CHOICES, null=False, blank=False)
    sample_name_field = models.BooleanField(default=False)
    pair_id_field = models.BooleanField(default=False)
    sample_type_field = models.BooleanField(default=False)
    sample_project_field = models.BooleanField(default=True)
    sex_in_desc = models.BooleanField(default=False)
    order_in_desc = models.BooleanField(default=False)
    referral_in_desc = models.BooleanField(default=False)
    hpo_in_desc = models.BooleanField(default=False)
    family_in_desc = models.BooleanField(default=False)
    sample_well_field = models.CharField(max_length=1, choices=SAMPLE_WELL_CHOICES, null=False, blank=False)
