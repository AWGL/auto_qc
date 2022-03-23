from django.contrib import admin
from .models import Assay, Index, IndexSet, IndexToIndexSet, Worksheet, ReferralType, SampleToWorksheet, Sample

# Register your models here.

class AssayAdmin(admin.ModelAdmin):
	list_display = ('assay_name',)
	search_fields = ['assay_name']

admin.site.register(Assay,AssayAdmin)


class IndexAdmin(admin.ModelAdmin):
	list_display = ('index_name',)
	search_fields = ['index_name']

admin.site.register(Index, IndexAdmin)


class IndexSetAdmin(admin.ModelAdmin):
	list_display = ('set_name',)
	search_fields = ['set_name']
	ordering = ['set_name']

admin.site.register(IndexSet,IndexSetAdmin)


admin.site.register(IndexToIndexSet)


class WorksheetAdmin(admin.ModelAdmin):
	list_display = ('worksheet_id', 'worksheet_test')
	search_fields = ['worksheet_id']
	ordering = ['worksheet_id']

admin.site.register(Worksheet,WorksheetAdmin)


admin.site.register(ReferralType)


admin.site.register(SampleToWorksheet)


class SampleAdmin(admin.ModelAdmin):
	list_display = ('sampleid',)
	search_fields = ['sampleid']
	ordering = ['sampleid']

admin.site.register(Sample,SampleAdmin)
