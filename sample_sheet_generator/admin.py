from django.contrib import admin

from .models import *

"""
Add the GLIMS samplesheet generators models to the Django admin page
Fields that can be searched by are defined in the search_fields variable
Fields displayed on the admin page are defined in the list_display variable
"""

class AssayAdmin(admin.ModelAdmin):
    list_display = ["assay", "lims_test"]
    search_fields = ["assay", "lims_test"]

admin.site.register(Assay, AssayAdmin)

class ReferralAdmin(admin.ModelAdmin):
    list_display = ["id", "referral_code", "referral_for_pipeline"]
    search_fields = ["id", "referral_code", "referral_for_pipeline"]

admin.site.register(Referral, ReferralAdmin)