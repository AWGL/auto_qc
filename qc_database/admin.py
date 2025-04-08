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
admin.site.register(DragenVariantCallingMetrics)
admin.site.register(DragenWGSCoverageMetrics)
admin.site.register(FusionContamination)
admin.site.register(FusionAlignmentMetrics)
admin.site.register(DragenPloidyMetrics)
admin.site.register(CalculatedSexMetrics)
admin.site.register(RelatednessQuality)
admin.site.register(Tso500Reads)
admin.site.register(CNVMetrics)
admin.site.register(SampleDragenFastqcData)

class DragenCNVMetricsAdmin(admin.ModelAdmin):
	raw_id_fields = ('sample_analysis',) 
	
admin.site.register(DragenCNVMetrics, DragenCNVMetricsAdmin)

class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('key', 'created_at', 'user', 'is_active')
    search_fields = ('key', 'user__username')
    readonly_fields = ('key', 'created_at')

admin.site.register(APIKey, APIKeyAdmin)