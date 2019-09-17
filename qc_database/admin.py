from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Run)
admin.site.register(WorkSheet)
admin.site.register(Sample)
admin.site.register(Pipeline)
admin.site.register(AnalysisType)
admin.site.register(RunAnalysis)
admin.site.register(SampleAnalysis)
