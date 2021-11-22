from django.contrib import admin
from .models import Assay, Index, IndexSet, IndexToIndexSet, Worksheet, ReferralType, SampleToWorksheet, Sample

# Register your models here.
admin.site.register(Assay)
admin.site.register(Index)
admin.site.register(IndexSet)
admin.site.register(IndexToIndexSet)
admin.site.register(Worksheet)
admin.site.register(ReferralType)
admin.site.register(SampleToWorksheet)
admin.site.register(Sample)
