from django import forms
from .models import  *
from django.urls import reverse
from crispy_forms.bootstrap import Field
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, HTML
from django.forms import ModelForm

class RunAnalysisSignOffForm(forms.Form):
	"""
	Form for signing off a run analysis
	"""
	approval = forms.ChoiceField(choices =(('Pass', 'Pass'), ('Fail', 'Fail')))
	comment = forms.CharField(widget=forms.Textarea(attrs={'rows':4}))

	def __init__(self, *args, **kwargs):
		
		self.run_analysis_id = kwargs.pop('run_analysis_id')
		self.comment = kwargs.pop('comment')
		super(RunAnalysisSignOffForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_id = 'run-analysis-signoff-form'
		self.helper.label_class = 'col-lg-2'
		self.fields['comment'].initial = self.comment
		self.helper.field_class = 'col-lg-8'
		self.helper.form_method = 'post'
		self.helper.add_input(Submit('run-analysis-signoff-form', 'Finalise', css_class='btn-success'))
		self.helper.form_class = 'form-horizontal'
		self.helper.layout = Layout(
			Field('approval', title=False),
			Field('comment', placeholder='Write a comment if you want.', title=False),
		)


class ResetRunForm(forms.Form):
	"""
	Form for resetting a run analysis
	"""

	def __init__(self, *args, **kwargs):
		
		self.run_analysis_id = kwargs.pop('run_analysis_id')

		super(ResetRunForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_id = 'reset-form'
		self.helper.label_class = 'col-lg-2'
		self.helper.field_class = 'col-lg-8'
		self.helper.form_method = 'post'
		self.helper.add_input(Submit('reset-form', 'Move To Pending', css_class='btn-success'))
		self.helper.form_class = 'form-horizontal'
		self.helper.layout = Layout(
		)


class SensitivityForm(ModelForm):

	class Meta:
		model = RunAnalysis
		fields = ['sensitivity', 'sensitivity_lower_ci', 'sensitivity_higher_ci']


	def __init__(self, *args, **kwargs):
		
		super(SensitivityForm, self).__init__(*args, **kwargs)
		self.helper = FormHelper()
		self.helper.form_id = 'reset-form'
		self.helper.label_class = 'col-lg-2'
		self.helper.field_class = 'col-lg-8'
		self.helper.form_method = 'post'
		self.helper.add_input(Submit('sensitivity-form', 'Submit Sensitivity', css_class='btn-success'))
		self.helper.form_class = 'form-horizontal'
		self.helper.layout = Layout(

		)