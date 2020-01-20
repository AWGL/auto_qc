from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Instrument)
admin.site.register(Run)
admin.site.register(InteropRunQuality)
admin.site.register(WorkSheet)
admin.site.register(Sample)
admin.site.register(Pipeline)
admin.site.register(AnalysisType)
admin.site.register(RunAnalysis)
admin.site.register(SampleAnalysis)
admin.site.register(SampleFastqcData)
admin.site.register(SampleHsMetrics)
admin.site.register(SampleDepthofCoverageMetrics)
admin.site.register(DuplicationMetrics)
admin.site.register(ContaminationMetrics)
admin.site.register(AlignmentMetrics)
admin.site.register(VariantCallingMetrics)
admin.site.register(InteropIndexMetrics)
admin.site.register(VCFVariantCount)
admin.site.register(DragenAlignmentMetrics)