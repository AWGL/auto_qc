from django import forms
from crispy_forms.bootstrap import StrictButton
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Div, Field, HTML

class UploadForm(forms.Form):
    """
    Form to upload GLIMS csv
    """
    
    SEQUENCER_CHOICES = (
        ("NovaSeq", "NovaSeq"),
        ("NextSeq", "NextSeq"),
        ("MiSeq", "MiSeq")
    )

    upload_file = forms.FileField(label="1. Upload your tsv")
    sequencer = forms.ChoiceField(choices=SEQUENCER_CHOICES, label="2. Select the sequencer")
    
    def __init__(self, *args, **kwargs):
        super(UploadForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "POST"
        #self.helper.add_input(
            #Submit("submit", "Create Samplesheet", css_class="btn btn-info w-100")
            #)
        self.helper.layout = Layout(
			Div(

					Div(
						Field('upload_file'),
					),
                    Div(
                        Field('sequencer')
                    ),
                    HTML('<br>'),
					Div(
						StrictButton(
							'<span class="fa fa-file-download" style="width:20px"></span>Download Locally', 
							css_class=f'btn-outline-light buttons1',
							type='submit', 
							name='download-samplesheet'
						),
						HTML('<br><br>'),
						StrictButton(
							'<span class="fa fa-file-download" style="width:20px"></span>Download to Webserver', 
							css_class=f'btn-outline-light buttons1',
							type='submit', 
							name='download-webserver'
						),
						css_class='col-4'
					)
			)
		)
