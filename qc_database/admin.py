from django.contrib import admin
from .models import *

# Custom admin classes with search functionality
class RunAdmin(admin.ModelAdmin):
    search_fields = ('run_id',)  # Basic search - adjust field names to match your model

class RunAnalysisAdmin(admin.ModelAdmin):
    search_fields = ('run__run_id',)  # Search by related fields

class DragenCNVMetricsAdmin(admin.ModelAdmin):
    raw_id_fields = ('sample_analysis',) 
    
class APIKeyAdmin(admin.ModelAdmin):
    list_display = ('key', 'created_at', 'user', 'is_active')
    search_fields = ('key', 'user__username')
    readonly_fields = ('key', 'created_at')

# Register models with custom admin classes
admin.site.register(Run, RunAdmin)
admin.site.register(RunAnalysis, RunAnalysisAdmin)
admin.site.register(DragenCNVMetrics, DragenCNVMetricsAdmin)
admin.site.register(APIKey, APIKeyAdmin)

# Register other models normally
admin.site.register(Instrument)
admin.site.register(InteropRunQuality)
admin.site.register(WorkSheet)
admin.site.register(Sample)
admin.site.register(Pipeline)
admin.site.register(AnalysisType)
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
admin.site.register(SomalierRelatedness)
admin.site.register(Tso500Reads)
admin.site.register(CNVMetrics)
admin.site.register(SampleDragenFastqcData)