from django import forms
from django.forms import ModelChoiceField
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Submit, HTML, Hidden, ButtonHolder, Fieldset
from crispy_forms.bootstrap import Field, FieldWithButtons, StrictButton

from sample_sheet.models import Index, IndexSet, SampleToWorksheet, ReferralType, Sample, IndexToIndexSet, Worksheet


class TechSettingsForm(forms.Form):
	"""
	"""

	sequencer = forms.ChoiceField(choices=Worksheet.SEQ_CHOICES + [('','--------')])
	index_set = forms.ModelChoiceField(
		queryset=IndexSet.objects.all().order_by('set_name'), 
		required=False, empty_label='Indexes not set up'
	)
	index = forms.ModelChoiceField(queryset=IndexToIndexSet.objects.all(), required=False, label="Start position")

	def __init__(self, *args, **kwargs):
		self.worksheet_obj = kwargs.pop('worksheet_obj')
		super(TechSettingsForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.fields['sequencer'].initial = None
		self.helper.form_id = 'tech-settings-form'
		self.helper.form_method = 'POST'
		self.helper.add_input(
			Submit('submit', 'Update', css_class='btn btn-outline-light w-25 buttons1')
		)
		self.helper.layout = Layout(
			Field('sequencer'),
			Field('index_set'),
			Field('index'),
			HTML('<br>'),
		)

		if 'index_set' in self.data:
			try:
				index_set_id = int(self.data.get('index_set'))
				self.fields['index'].queryset = IndexToIndexSet.objects.filter(index_set=index_set_id).order_by('pk')
			except (ValueError, TypeError):
				pass  # invalid input, shouldn't exist as fed from modelchoicefield
			self.fields['index'].queryset = IndexToIndexSet.objects.all()


class EditIndexForm(forms.Form):
	pos = forms.IntegerField(min_value=1)
	# pool = forms.ChoiceField(choices=SampleToWorksheet.POOL_CHOICES)
	i7_index = forms.ModelChoiceField(queryset=Index.objects.filter(i7_or_i5='i7'))
	i5_index = forms.ModelChoiceField(queryset=Index.objects.filter(i7_or_i5='i5'), required = False)


	def __init__(self, *args, **kwargs):
		self.sample_index_obj = kwargs.pop('sample_index_obj')
		super(EditIndexForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.fields['pos'].initial = self.sample_index_obj.pos
		self.fields['i7_index'].initial = self.sample_index_obj.index1
		self.fields['i5_index'].initial = self.sample_index_obj.index2
		# index_options = IndexToIndexSet.objects.filter(index_set= self.sample_index_obj.worksheet.index_set).values_list('index1', 'index1_id')
		# self.fields['i7_index'].choices = index_options
		# self.fields['pool'].initial = self.sample_index_obj.pool
		self.helper.form_id = 'index-settings-form'
		self.helper.form_method = 'POST'
		self.helper.add_input(
			Submit('submit', 'Update', css_class='btn btn-outline-light w-25 buttons1')
		)
		self.helper.layout = Layout(
			Hidden('sample_index_obj', self.sample_index_obj.id),
			Hidden('pos', self.sample_index_obj.pos),
			# Field('pool'),
			Field('i7_index'),
			Field('i5_index'),
			HTML('<br>'),
		)


class EditSampleNotesForm(forms.Form):
	pos = forms.IntegerField(min_value=1)
	samplenotes = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label = "Note:")

	def __init__(self, *args, **kwargs):
		self.sample_notes_obj = kwargs.pop('sample_notes_obj')
		super(EditSampleNotesForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.fields['pos'].initial = self.sample_notes_obj.pos
		self.fields['samplenotes'].initial = self.sample_notes_obj.notes
		self.helper.form_id = 'sample-notes-form'
		self.helper.form_method = 'POST'
		self.helper.add_input(
			Submit('submit', 'Update', css_class='btn btn-outline-light w-25 buttons1')
		)
		self.helper.layout = Layout(
			Hidden('sample_notes_obj', self.sample_notes_obj.id),
			Hidden('pos', self.sample_notes_obj.pos),
			Field('samplenotes'),
		)


class EditSampleDetailsForm(forms.Form):
	urgent = forms.BooleanField(label="Tick if this sample is urgent and requires rapid WGS", required=False)
	pos = forms.IntegerField(min_value=1)
	referral_type = forms.ModelChoiceField(queryset=ReferralType.objects.all(), label="Referral Type")
	gender = forms.ChoiceField(choices=Sample.SEX_CHOICES, label="Gender")
	hpo_ids = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label = "HPO IDs (seperated with a comma)", required=False)

	def __init__(self, *args, **kwargs):
		self.sample_details_obj = kwargs.pop('sample_details_obj')
		super(EditSampleDetailsForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.fields['pos'].initial = self.sample_details_obj.pos
		self.fields['gender'].initial = self.sample_details_obj.sample.sex
		self.fields['referral_type'].initial = self.sample_details_obj.referral
		self.fields['hpo_ids'].initial = self.sample_details_obj.hpo_ids
		referral_choices = ReferralType.objects.filter(assay = self.sample_details_obj.worksheet.worksheet_test).order_by('name').values_list('name', 'name')
		self.fields['referral_type'].choices = (*referral_choices,)
		self.fields['urgent'].initial = self.sample_details_obj.urgent
		self.helper.form_id = 'sample-details-form'
		self.helper.form_method = 'POST'
		self.helper.add_input(
			Submit('submit', 'Update', css_class='btn btn-outline-light w-25 buttons1')
		)
		# if wgs then show hpo option and urgent option
		if str(self.sample_details_obj.worksheet.worksheet_test) in (['WGS']):

			self.helper.layout = Layout(
				Field('urgent'),
				Hidden('sample_details_obj', self.sample_details_obj.id),
				Hidden('pos', self.sample_details_obj.pos),
				Field('referral_type'),
				Field('hpo_ids'),
				Field('gender'),
			)

		# if wes then show hpo option
		elif str(self.sample_details_obj.worksheet.worksheet_test) in (['WES']):

			self.helper.layout = Layout(
				Hidden('urgent', self.sample_details_obj.urgent),
				Hidden('sample_details_obj', self.sample_details_obj.id),
				Hidden('pos', self.sample_details_obj.pos),
				Field('referral_type'),
				Field('hpo_ids'),
				Field('gender'),
			)

		else:
			self.helper.layout = Layout(
				Hidden('urgent', self.sample_details_obj.urgent),
				Hidden('sample_details_obj', self.sample_details_obj.id),
				Hidden('pos', self.sample_details_obj.pos),
				Field('referral_type'),
				Hidden('hpo_ids', None),
				Field('gender'),
			)


class CreateFamilyForm(forms.Form):
	familyid = forms.ChoiceField(choices=Sample.FAMILYID_CHOICES)
	fatherid = forms.ChoiceField(choices=[], label = 'Father sample ID', required=False)
	motherid = forms.ChoiceField(choices=[], label = 'Mother sample ID', required=False)
	probandid = forms.ChoiceField(choices=[], label = 'Proband sample ID')

	def __init__(self, *args, **kwargs):
		self.worksheet_obj = kwargs.pop('worksheet_obj')
		super(CreateFamilyForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.fields['familyid'].initial = None
		sampleid_set = SampleToWorksheet.objects.filter(worksheet_id = self.worksheet_obj).values_list('sample', 'sample_id')
		sampleid_set_plus_null = tuple([(None, '----')] + list(sampleid_set))
		self.fields['fatherid'].choices = (sampleid_set_plus_null)
		self.fields['fatherid'].initial = None
		self.fields['motherid'].choices = (sampleid_set_plus_null)
		self.fields['motherid'].initial = None
		self.fields['probandid'].choices = (*sampleid_set,)
		self.fields['probandid'].initial = None
		self.helper.form_id = 'create-family-form'
		self.helper.form_method = 'POST'
		self.helper.add_input(
			Submit('submit', 'Create', css_class='btn btn-outline-light w-25 buttons1')
		)
		self.helper.layout = Layout(
			Field('familyid'),
			Field('probandid'),
			Field('fatherid'),
			Field('motherid'),
		)


class ClearFamilyForm(forms.Form):
	clear_family_check = forms.BooleanField(required=False, label = 'I am sure.')

	def __init__(self, *args, **kwargs):
		self.worksheet_obj = kwargs.pop('worksheet_obj')
		super(ClearFamilyForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.fields['clear_family_check'].initial = False
		self.helper.form_id = 'clear-family-form'
		self.helper.form_method = 'POST'
		self.helper.layout = Layout(
			Div(
				Div(
					Field('clear_family_check'),
						style="text-align: center"
					),
				Div(
					ButtonHolder(
						Submit('submit', 'Clear family data', css_class='btn btn-danger w-25')
						),
						style="text-align: center"
					)
					),
				)


class ClearUrgentForm(forms.Form):
	clear_urgent_check = forms.BooleanField(required=False, label = 'I am sure.')

	def __init__(self, *args, **kwargs):
		self.worksheet_obj = kwargs.pop('worksheet_obj')
		super(ClearUrgentForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.fields['clear_urgent_check'].initial = False
		self.helper.form_id = 'clear-urgent-form'
		self.helper.form_method = 'POST'
		self.helper.layout = Layout(
			Div(
				Div(
					Field('clear_urgent_check'),
						style="text-align: center"
					),
				Div(
					ButtonHolder(
						Submit('submit', 'Clear urgent data', css_class='btn btn-danger w-25')
						),
						style="text-align: center"
					)
					),
				)


class ClinSciSignoffForm(forms.Form):

	clinsci_worksheet_checked = forms.BooleanField(required=False, label = 'Manual check')
	sex_checked = forms.BooleanField(required=False, label = 'Sex check')
	hpo_checked = forms.BooleanField(required=False, label = 'HPO check')
	family_checked = forms.BooleanField(required=False, label = 'Family check')
	urgency_checked = forms.BooleanField(required=False, label= 'Urgency check')

	def __init__(self, *args, **kwargs):
		self.worksheet_obj = kwargs.pop('worksheet_obj')
		super(ClinSciSignoffForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.fields['clinsci_worksheet_checked'].initial = False
		self.helper.form_id = 'cs-signoff-form'
		self.helper.form_method = 'POST'
		self.helper.layout = Layout(
			Div(
				Div(
					Field('clinsci_worksheet_checked'),
						style="text-align: center"
					),
				Div(
					Field('sex_checked'),
						style="text-align: center"
					),
				Div(
					Field('hpo_checked'),
						style="text-align: center"
					),
				Div(
					Field('family_checked'),
						style="text-align: center"
					),
				Div(
					Field('urgency_checked'),
					style="text-align: center"
				),
				Div(
					ButtonHolder(
						Submit('submit', 'Sign Off', css_class='btn btn-success w-50')
						),
						style="text-align: center"
					)
					),
				)


class ClinSciOpenWorksheetForm(forms.Form):
	clinsci_reopen_check = forms.BooleanField(required=False, label = 'I am sure.')

	def __init__(self, *args, **kwargs):
		self.worksheet_obj = kwargs.pop('worksheet_obj')
		super(ClinSciOpenWorksheetForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.fields['clinsci_reopen_check'].initial = False
		self.helper.form_id = 'cs-reopen-form'
		self.helper.form_method = 'POST'
		self.helper.layout = Layout(
			Div(
				Div(
					Field('clinsci_reopen_check'),
						style="text-align: center"
					),
				Div(
					ButtonHolder(
						Submit('submit', 'Re-open worksheet', css_class='btn btn-danger w-25')
						),
						style="text-align: center"
					)
					),
				)


class TechteamSignoffForm(forms.Form):
	techteam_worksheet_checked = forms.BooleanField(required=False, label = 'Manual check')

	def __init__(self, *args, **kwargs):
		self.worksheet_obj = kwargs.pop('worksheet_obj')
		super(TechteamSignoffForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.fields['techteam_worksheet_checked'].initial = False
		self.helper.form_id = 'tech-signoff-form'
		self.helper.form_method = 'POST'
		self.helper.layout = Layout(
			Div(
				Div(
					Field('techteam_worksheet_checked'),
						style="text-align: center"
					),
				Div(
					ButtonHolder(
						Submit('submit', 'Sign Off', css_class='btn btn-success w-25')
						),
						style="text-align: center"
					)
					),
				)


class TechteamOpenWorksheetForm(forms.Form):
	techteam_reopen_check = forms.BooleanField(required=False, label = 'I am sure.')

	def __init__(self, *args, **kwargs):
		self.worksheet_obj = kwargs.pop('worksheet_obj')
		super(TechteamOpenWorksheetForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.fields['techteam_reopen_check'].initial = False
		self.helper.form_id = 'tech-reopen-form'
		self.helper.form_method = 'POST'
		self.helper.layout = Layout(
			Div(
				Div(
					Field('techteam_reopen_check'),
						style="text-align: center"
					),
				Div(
					ButtonHolder(
						Submit('submit', 'Re-open worksheet', css_class='btn btn-danger w-25')
						),
						style="text-align: center"
					)
					),
				)


class ResetIndexForm(forms.Form):
	reset_index_check = forms.BooleanField(required=False, label = 'I am sure.')

	def __init__(self, *args, **kwargs):
		self.worksheet_obj = kwargs.pop('worksheet_obj')
		super(ResetIndexForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.fields['reset_index_check'].initial = False
		self.helper.form_id = 'reset-index-form'
		self.helper.form_method = 'POST'
		self.helper.layout = Layout(
			Div(
				Div(
					Field('reset_index_check'),
						style="text-align: center"
					),
				Div(
					ButtonHolder(
						Submit('submit', 'Reset all indexes', css_class='btn btn-danger w-25')
						),
						style="text-align: center"
					)
					),
				)


class uploadQuery(forms.Form):
	"""
	form to upload shire query
	"""
	select_upload_file = forms.FileField()


	def __init__(self, *args, **kwargs):
		super(uploadQuery, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_method = 'post'
		self.helper.form_id = 'upload-form'
		self.helper.label_class = 'col-2'
		self.helper.field_class = 'col-10'
		self.helper.form_class = 'form-horizontal'
		self.helper.layout = Layout(
			Div(

					Div(
						Field('select_upload_file'),
						style="width: 100%; margin: 0 auto"
					),
					Div(
						ButtonHolder(
							Submit('submit', 'Submit', css_class='btn-outline-light buttons1')
						),
						style="width: 10%; margin: 0 auto; text-align: left"
					),
					style="text-align: right"
			))


class DownloadSamplesheetButton(forms.Form):
	"""
	Button to download samplesheet. Renders in an alert box which changes colour depending on the status
	of the samplesheet checks - green if complete and red if not
	"""
	additional_worksheet = ModelChoiceField(queryset=Worksheet.objects.filter(clinsci_signoff_complete = True, techteam_signoff_complete = True).order_by('-worksheet_id'), required=False, label="Available worksheets")

	def __init__(self, *args, **kwargs):
		# get if coupled worksheets required or not
		self.assay_obj = kwargs.pop('assay_obj')
		self.coupled_worksheets = self.assay_obj.enable_coupled_worksheets

		# get variable from view - whether or not all checks are complete
		self.checks_complete = kwargs.pop('checks_complete')

		super(DownloadSamplesheetButton, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_method = 'POST'

		# get assay to couple if coupled worksheets is True
		if self.coupled_worksheets:
			coupled_worksheet_assay = self.assay_obj.coupled_worksheet_assay

			# create and overwrite form choices
			worksheet_choices = list(Worksheet.objects.filter(worksheet_test = coupled_worksheet_assay, clinsci_signoff_complete = True, techteam_signoff_complete = True).order_by('-worksheet_id').values_list('worksheet_id','worksheet_id'))
			worksheet_choices_incnull = [('','')] + worksheet_choices
			self.fields['additional_worksheet'].choices = worksheet_choices_incnull
			self.fields['additional_worksheet'].initial = None

		# render form differently depending on whether or not the checks are complete
		if self.checks_complete:
			message = '<span class="fa fa-check-circle" style="width:20px;color:green"></span>Samplesheet has been checked.'
			message_class = 'success'
		else:
			message = '<span class="fa fa-times-circle" style="width:20px;color:red"></span>The checks are not complete.'
			message_class = 'danger disabled'

		# make layout
		# if coupled worksheets = True, add additional worksheet
		if self.coupled_worksheets:
			self.helper.layout = Layout(
				Div(
					Field('additional_worksheet'),
					Div(
						Div(
							HTML(f'{message}'),
							css_class='col-8'
						),
						Div(
							StrictButton(
								'<span class="fa fa-file-download" style="width:20px"></span>Download Locally', 
								css_class=f'btn btn-{message_class} btn-sm w-100',
								type='submit', 
								name='download-samplesheet'
							),
							HTML('<br><br>'),
							StrictButton(
								'<span class="fa fa-file-download" style="width:20px"></span>Download to Webserver', 
								css_class=f'btn btn-{message_class} btn-sm w-100',
								type='submit', 
								name='download-webserver'
							),
							css_class='col-4'
						),
						css_class='row'
					), 
					css_class=f'container alert alert-{message_class}'
				)
			)

		# hide additional worksheet field if coupled_worksheets = False
		else:
			self.helper.layout = Layout(
				Div(
					Hidden('additional_worksheet', ''),
					Div(
						Div(
							HTML(f'{message}'),
							css_class='col-8'
						),
						Div(
							StrictButton(
								'<span class="fa fa-file-download" style="width:20px"></span>Download Locally', 
								css_class=f'btn btn-{message_class} btn-sm w-100',
								type='submit', 
								name='download-samplesheet'
							),
							HTML('<br><br>'),
							StrictButton(
								'<span class="fa fa-file-download" style="width:20px"></span>Download to Webserver', 
								css_class=f'btn btn-{message_class} btn-sm w-100',
								type='submit', 
								name='download-webserver'
							),
							css_class='col-4'
						), 
					css_class=f'container alert alert-{message_class} row'
					)
				)
			)


class AdvancedDownloadForm(forms.Form):

	advanced_download_text = forms.CharField(widget=forms.Textarea(attrs={'rows':6}), label = "Worksheet ID list")

	def __init__(self, *args, **kwargs):
		self.worksheet_obj = kwargs.pop('worksheet_obj')

		super(AdvancedDownloadForm, self).__init__(*args, **kwargs)
		self.fields['advanced_download_text'].initial = f"{self.worksheet_obj.worksheet_id},"
		self.helper = FormHelper()
		self.helper.form_method = 'post'
		self.helper.layout = Layout(
			Div(

					Div(
						Field('advanced_download_text'),
					),
					Div(
						StrictButton(
							'<span class="fa fa-file-download" style="width:20px"></span>Download Locally', 
							css_class=f'btn-outline-light buttons1',
							type='submit', 
							name='advanced-download-samplesheet'
						),
						HTML('<br><br>'),
						StrictButton(
							'<span class="fa fa-file-download" style="width:20px"></span>Download to Webserver', 
							css_class=f'btn-outline-light buttons1',
							type='submit', 
							name='advanced-download-webserver'
						),
						css_class='col-4'
					)
			)
		)