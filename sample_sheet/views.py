from io import StringIO, TextIOWrapper
from datetime import datetime
from itertools import cycle, islice


from django.shortcuts import render, get_object_or_404
from django.core.management import call_command
from django.http import HttpResponse
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.contrib.messages import get_messages
from sample_sheet.utils import import_worksheet_data
from sample_sheet.models import Assay, IndexSet, Worksheet, SampleToWorksheet, IndexToIndexSet, Index, Sample
from .forms import TechSettingsForm, DownloadSamplesheetButton, EditIndexForm, uploadQuery, EditSampleNotesForm, ClinSciSignoffForm, ClinSciOpenWorksheetForm, TechteamSignoffForm, TechteamOpenWorksheetForm, EditSampleDetailsForm, ResetIndexForm, CreateFamilyForm, ClearFamilyForm

########## home page ################
@transaction.atomic
@login_required
def home(request):
	return render(request, 'sample_sheet/home.html')

############## upload ################
@transaction.atomic
@login_required
def upload(request):

	form = uploadQuery()
	context = {
				'form' : form,
				'error' : None,
				'success' : None,
				'assay' : None,
				'worksheet_id' : None
	}

	if request.POST:
		
		form = uploadQuery(request.POST, request.FILES)
		print(request.POST)
		if form.is_valid():
			
			raw_file = request.FILES['select_upload_file']
			utf_file = TextIOWrapper(raw_file, encoding='utf-8')

			# try running import script. The script is coded to return upload_complete = False if a specific error occurs
			try:                
				upload_complete, message, worksheet_id, assay_name = import_worksheet_data(utf_file)
				if upload_complete:
					context['success'] = f'Worksheet {worksheet_id} upload is complete'
					context['assay'] = assay_name
					context['worksheet_id'] = worksheet_id
					print('import ok')
				else:
					context['error'] = message
					print('import failed due to logic checks')
				
			# if script fails, error.
			except:
				print('did not upload ok due to script error')
				context['error'] = 'An unknown error occurred, please check your input file or contact Bioinformatics'

	return render(request, 'sample_sheet/upload.html', context)


############### Index pages #################
@transaction.atomic
@login_required
def index_sets(request):
	"""
	"""
	# get all index sets
	index_sets = IndexSet.objects.all()

	context = {
		'index_sets': index_sets
	}

	return render(request, 'sample_sheet/index_sets.html', context)

@transaction.atomic
@login_required
def index_detail(request, index_set_name):
	"""
	"""
	# get all index sets
	index_set_query = IndexSet.objects.get(set_name=index_set_name)

	index_list = []
	for index in index_set_query.get_vendor_index_set():
		if index.index2:
			temp_dict = {
				'pos': index.index_pos,
				'index1_name': index.index1.index_name,
				'index1_seq': index.index1.sequence,
				'index2_name': index.index2.index_name,
				'index2_seq': index.index2.sequence
			}
			index_list.append(temp_dict)

		else:
			temp_dict = {
				'pos': index.index_pos,
				'index1_name': index.index1.index_name,
				'index1_seq': index.index1.sequence,
				'index2_name': '-',
				'index2_seq': '-'
			}
			index_list.append(temp_dict)

	context = {
		'name': index_set_query.set_name,
		'indexes': index_list
	}
	return render(request, 'sample_sheet/indexes.html', context)


############# samplesheet pages ################
def get_sample_info(worksheet_obj):
	samples = worksheet_obj.get_samples_from_ws()

	'''
	samples example
	{'1': {
		'sample': '20M12346', 
		'referral': 'null', 
		'notes': None, 
		'sex': 'Unknown', 
		'index1': <Index: B01_i7>, 
		'index2': <Index: B02_i5>, 
		'pool': 'Y', 
		'sample_obj': <SampleToWorksheet: 1_20-456_20M12346>, 
		'edited': True
		}, 
	'2': {
		'sample': '20M12348', 
		'referral': 'null', 
		'notes': 'sample and worksheet specific notes blah blah blah', 
		'sex': 'Unknown', 
		'index1': <Index: B02_i7>, 
		'index2': <Index: B02_i5>, 
		'pool': 'Y', 
		'sample_obj': <SampleToWorksheet: 2_20-456_20M12348>, 
		'edited': False
		},

		etc...

	'''
	# add index and notes form to each sample
	for k, v in samples.items():
		v['indexform'] = EditIndexForm(sample_index_obj=v['sample_obj'])
		v['notesform'] = EditSampleNotesForm(sample_notes_obj=v['sample_obj'])
		v['detailsform'] = EditSampleDetailsForm(sample_details_obj=v['sample_obj'])
		
		samples[k] = v

	'''
	samples example after edit with forms
	{'1': {
		'sample': '20M12346', 
		'referral': 'null', 
		'notes': None, 
		'sex': 'Unknown', 
		'index1': <Index: B01_i7>, 
		'index2': <Index: B02_i5>, 
		'pool': 'Y', 
		'sample_obj': <SampleToWorksheet: 1_20-456_20M12346>, 
		'edited': True, 
		'indexform': <EditIndexForm bound=False, valid=Unknown, fields=(pos;i7_index;i5_index;pool)>, 
		'notesform': <EditSampleNotesForm bound=False, valid=Unknown, fields=(pos;samplenotes)>
		}, 
	'2': {
		'sample': '20M12348', 
		'referral': 'null', 
		'notes': 'sample and worksheet specific notes blah blah blah', 
		'sex': 'Unknown', 
		'index1': <Index: B02_i7>, 
		'index2': <Index: B02_i5>, 
		'pool': 'Y', 
		'sample_obj': <SampleToWorksheet: 2_20-456_20M12348>, 
		'edited': False, 
		'indexform': <EditIndexForm bound=False, valid=Unknown, fields=(pos;i7_index;i5_index;pool)>, 
		'notesform': <EditSampleNotesForm bound=False, valid=Unknown, fields=(pos;samplenotes)>
		}

		etc...

	'''

	return samples

@transaction.atomic
@login_required
def view_worksheets(request, service_slug):
	"""
	"""

	# get assay config
	assay = get_object_or_404(Assay, assay_slug = service_slug)

	# get all worksheets from selected service
	worksheets = Worksheet.objects.filter(worksheet_test = assay).order_by('-worksheet_id')
	

	ws_list = []
	for w in worksheets:
		ws_list.append({
			'worksheet_id' : w.worksheet_id,
			'upload_date' : w.upload_date,
			'status' : w.get_ws_status(),
			})


	context = {
		'worksheet_list' : ws_list,
		'worksheets' : worksheets,
		'assay' : assay,
	}

	return render(request, 'sample_sheet/view_worksheets.html', context)

@transaction.atomic
@login_required
def view_worksheet_samples(request, service_slug, worksheet_id):
	"""
	"""
	# get worksheet/ assay/ samples objects
	worksheet_obj = Worksheet.objects.get(worksheet_id = worksheet_id)
	# worksheet_obj = 20-456
	assay = Assay.objects.get(assay_slug = service_slug)
	samples = get_sample_info(worksheet_obj)
	'''
	samples example:
	{'1': {
		'sample': '20M12346', 
		'referral': 'null', 
		'notes': None, 
		'sex': 'Unknown', 
		'index1': <Index: B01_i7>, 
		'index2': <Index: B02_i5>, 
		'pool': 'Y', 
		'sample_obj': <SampleToWorksheet: 1_20-456_20M12346>, 
		'edited': True, 
		'indexform': <EditIndexForm bound=False, valid=Unknown, fields=(pos;i7_index;i5_index;pool)>, 
		'notesform': <EditSampleNotesForm bound=False, valid=Unknown, fields=(pos;samplenotes)>
		}, 
	'2': {
		'sample': '20M12348', 
		'referral': 'null', 
		'notes': 'sample and worksheet specific notes blah blah blah', 
		'sex': 'Unknown', 
		'index1': <Index: B02_i7>, 
		'index2': <Index: B02_i5>, 
		'pool': 'Y', 
		'sample_obj': <SampleToWorksheet: 2_20-456_20M12348>, 
		'edited': False, 
		'indexform': <EditIndexForm bound=False, valid=Unknown, fields=(pos;i7_index;i5_index;pool)>, 
		'notesform': <EditSampleNotesForm bound=False, valid=Unknown, fields=(pos;samplenotes)>
		}

		etc...
	}

   '''

	################## tech team status ###################
	## get auto checks for techteam. Returns dictionary eg:
	# {'techteam_autochecks_overall': 'complete', 'techteam_manualchecks_overall': 'incomplete', 'techteam_checks_overall': 'incomplete'}
	techteam_check_status = Worksheet.get_techteam_check_status(worksheet_id)


	############ clin sci status ##################
	## get auto checks for clinsci. Returns dictionary eg:
	# {'clinsci_autochecks_overall': 'complete', 'clinsci_manualchecks_overall': 'incomplete', 'clinsci_checks_overall': 'incomplete'}
	clinsci_check_status = Worksheet.get_clinsci_check_status(worksheet_id)


	## lookup dictionary to render tick/cross etc, depending on status
	status_html_lookup = {
		'complete': '<span class="fa fa-check" style="width:20px;color:green"></span>',
		'incomplete': '<span class="fa fa-times" style="width:20px;color:red"></span>',
	}

	## get correct download button, depending on status
	if clinsci_check_status['clinsci_checks_overall'] == 'complete' and techteam_check_status['techteam_checks_overall'] == 'complete': 
		download_form = DownloadSamplesheetButton(checks_complete=True)
	else:
		download_form = DownloadSamplesheetButton(checks_complete=False)


	## add to context dict for template
	context = {
		'worksheet_info': {
			'worksheet_id': worksheet_obj.worksheet_id,
			'index_set': worksheet_obj.index_set,
			'assay_name': assay.assay_name,
			'assay_slug': assay.assay_slug,
			'clinsci_signoff_name': worksheet_obj.clinsci_signoff_name,
			'clinsci_signoff_datetime' : worksheet_obj.clinsci_signoff_datetime,
			'clinsci_signoff_complete' : worksheet_obj.clinsci_signoff_complete,
			'techteam_signoff_name': worksheet_obj.techteam_signoff_name,
			'techteam_signoff_datetime' : worksheet_obj.techteam_signoff_datetime,
			'techteam_signoff_complete' : worksheet_obj.techteam_signoff_complete,
		},
		'sample_data': samples,
		'worksheet_checks': {
			'clin_sci': {
				'overall': clinsci_check_status['clinsci_checks_overall'],
				'status_html': status_html_lookup[ clinsci_check_status['clinsci_checks_overall'] ],
				'autochecks': status_html_lookup[ clinsci_check_status['clinsci_autochecks_overall'] ],
			},
			'tech_team': {
				'overall': techteam_check_status['techteam_checks_overall'],
				'status_html': status_html_lookup[ techteam_check_status['techteam_checks_overall'] ],
				'autochecks': status_html_lookup[ techteam_check_status['techteam_autochecks_overall'] ],
			},
		},
		'tech_settings_form': TechSettingsForm(worksheet_obj=worksheet_obj),
		'download_form': download_form,
		'clinsci_signoff_form' : ClinSciSignoffForm(worksheet_obj=worksheet_obj),
		'clinsci_reopen_form' : ClinSciOpenWorksheetForm(worksheet_obj=worksheet_obj),
		'techteam_signoff_form' : TechteamSignoffForm(worksheet_obj=worksheet_obj),
		'techteam_reopen_form' : TechteamOpenWorksheetForm(worksheet_obj=worksheet_obj),
		'reset_index_form' : ResetIndexForm(worksheet_obj=worksheet_obj),
		'create_family_form' : CreateFamilyForm(worksheet_obj=worksheet_obj),
		'clear_family_form' : ClearFamilyForm(worksheet_obj=worksheet_obj),
	}


	## when request is submitted
	if request.method == 'POST':

		## if tech setting form is submitted
		if 'index_set' in request.POST:

			tech_settings_form = TechSettingsForm(request.POST, worksheet_obj=worksheet_obj)
			# print(tech_settings_form.errors)


			if tech_settings_form.is_valid():
				cleaned_data = tech_settings_form.cleaned_data

				## only update data if all parts of form filled in
				if cleaned_data['index_set'] and cleaned_data['index']:

					## update worksheet info
					worksheet_obj.index_set = cleaned_data['index_set']

					## Add index to each sample
					samples = SampleToWorksheet.objects.filter(worksheet_id = worksheet_id).order_by('pos')
					index_set_obj = IndexToIndexSet.objects.filter(index_set=cleaned_data['index_set']).order_by('index_pos')
					print(index_set_obj)

					# clear old indexes if exist
					for s in samples:
						s.index1, s.index2, s.edited = None, None, False
						s.save()


					## add new indexes
					## calculate start position, allow for 0 indexing
					start_pos = cleaned_data['index'].index_pos - 1

					## iterate through until start reached then 
					for s, i in zip(samples, islice(cycle(index_set_obj),start_pos, None)):
						s.index1 = i.index1
						if i.index2:
							s.index2 = i.index2
						s.save()

					## save worksheet changes to db
					worksheet_obj.save()


					# reload context
					worksheet_obj = Worksheet.objects.get(worksheet_id = worksheet_id)
					context['worksheet_info']['index_set'] = worksheet_obj.index_set
					context['sample_data'] = get_sample_info(worksheet_obj)
					context['tech_settings_form'] = TechSettingsForm(worksheet_obj=worksheet_obj)

					# check status for techteam
					techteam_check_status = Worksheet.get_techteam_check_status(worksheet_id)
					context['worksheet_checks']['tech_team']['autochecks'] = status_html_lookup[ techteam_check_status['techteam_autochecks_overall'] ]



		## if index edit form is submitted
		if 'pool' in request.POST:

			# get sample worksheet object of the sample that was submitted
			sample_ws_obj = SampleToWorksheet.objects.get(id=request.POST['sample_index_obj'])

			edit_form = EditIndexForm(request.POST, sample_index_obj=sample_ws_obj)

			if edit_form.is_valid():
				cleaned_data = edit_form.cleaned_data
				edited = False

				if cleaned_data['pool'] != sample_ws_obj.pool:
					sample_ws_obj.pool = cleaned_data['pool']
					edited = True

				if cleaned_data['i7_index'] != sample_ws_obj.index1:
					sample_ws_obj.index1 = cleaned_data['i7_index']
					edited = True

				if cleaned_data['i5_index'] != sample_ws_obj.index2:
					sample_ws_obj.index2 = cleaned_data['i5_index']
					edited = True

				## save and mark as edited
				if edited:
					sample_ws_obj.edited = True
					sample_ws_obj.save()

				## check to see if any indexes have been skipped
				if cleaned_data['pool'] == "N1":
					print('index is skipped somewhere')

					## trigger function to reload indexes


				## reload context
				context['sample_data'] = get_sample_info(worksheet_obj)

				# check status for techteam
				techteam_check_status = Worksheet.get_techteam_check_status(worksheet_id)
				context['worksheet_checks']['tech_team']['autochecks'] = status_html_lookup[ techteam_check_status['techteam_autochecks_overall'] ]


		## if reset indexes is submitted
		if 'reset_index_check' in request.POST:

			reset_form = ResetIndexForm(request.POST, worksheet_obj=worksheet_obj)

			if reset_form.is_valid():
				cleaned_data = reset_form.cleaned_data

				## only change data is tick box was checked (AKA == True)
				if cleaned_data['reset_index_check']:

					## overwrite worksheet obj with null for index set and sequencer
					worksheet_obj.index_set = None
					worksheet_obj.save()

					## iterate through samples and change all relevant pieces to blank or default
					samples = SampleToWorksheet.objects.filter(worksheet=worksheet_obj).order_by('pos')

					for s in samples:
						s.index1, s.index2, s.edited, s.pool = None, None, False, 'Y'
						s.save()

					## reload context for ws
					context['worksheet_info']['index_set'] = worksheet_obj.index_set
					
					## reload context for sample
					context['sample_data'] = get_sample_info(worksheet_obj)

					# check status for techteam autocheck
					techteam_check_status = Worksheet.get_techteam_check_status(worksheet_id)
					context['worksheet_checks']['tech_team']['autochecks'] = status_html_lookup[ techteam_check_status['techteam_autochecks_overall'] ]


		## if notes edit form is submitted
		if 'samplenotes' in request.POST:
			sample_ws_obj = SampleToWorksheet.objects.get(id=request.POST['sample_notes_obj'])
			edit_notes = EditSampleNotesForm(request.POST, sample_notes_obj=sample_ws_obj)

			if edit_notes.is_valid():
				cleaned_data = edit_notes.cleaned_data

				# edit notes if changed
				if cleaned_data['samplenotes'] != sample_ws_obj.notes:
					sample_ws_obj.notes = cleaned_data['samplenotes']
					sample_ws_obj.save()

				#reload context
				worksheet_obj = Worksheet.objects.get(worksheet_id = worksheet_id)
				context['sample_data'] = get_sample_info(worksheet_obj)


		## if details edit form is submitted
		if 'gender' in request.POST:
			sample_ws_obj = SampleToWorksheet.objects.get(id=request.POST['sample_details_obj'])
			edit_details = EditSampleDetailsForm(request.POST, sample_details_obj=sample_ws_obj)
			
			if edit_details.is_valid():
				cleaned_data = edit_details.cleaned_data

				# edit notes if changed
				if cleaned_data['referral_type'] != sample_ws_obj.referral:
					sample_ws_obj.referral = cleaned_data['referral_type']
					sample_ws_obj.save()

				# if sample sex has changed then change and save the worksheet.sample instance
				if cleaned_data['gender'] != sample_ws_obj.sample.sex:
					sample_ws_obj.sample.sex = cleaned_data['gender']
					sample_ws_obj.sample.save()

				#reload context
				worksheet_obj = Worksheet.objects.get(worksheet_id = worksheet_id)
				context['sample_data'] = get_sample_info(worksheet_obj)


		## if create family form submitted
		if 'probandid' in request.POST:

			create_family_form = CreateFamilyForm(request.POST, worksheet_obj= worksheet_obj)

			if create_family_form.is_valid():
				cleaned_data = create_family_form.cleaned_data

				## check that three unique sampleid are selected.
				if cleaned_data['fatherid'] == cleaned_data['motherid'] or cleaned_data['fatherid'] == cleaned_data['probandid'] or cleaned_data['motherid'] == cleaned_data['probandid']:
					print('selected samples were not unique')
					print(cleaned_data)

				## check familyid was selected
				elif cleaned_data['familyid'] == None:
					print('familyid not selected')

				else:
					print('samples were unique and family id selected')

					## edit father details
					fathersample_obj = Sample.objects.get(sampleid = cleaned_data['fatherid'])
					fathersample_obj.familyid = cleaned_data['familyid']
					fathersample_obj.familypos = 'Father'
					fathersample_obj.affected = False
					fathersample_obj.save()

					## edit mother details
					mothersample_obj = Sample.objects.get(sampleid = cleaned_data['motherid'])
					mothersample_obj.familyid = cleaned_data['familyid']
					mothersample_obj.familypos = 'Mother'
					mothersample_obj.affected = False
					mothersample_obj.save()

					## edit proband details
					probandsample_obj = Sample.objects.get(sampleid = cleaned_data['probandid'])
					probandsample_obj.familyid = cleaned_data['familyid']
					probandsample_obj.familypos = 'Proband'
					probandsample_obj.affected = True
					probandsample_obj.save()
					
					## reload context
					worksheet_obj = Worksheet.objects.get(worksheet_id = worksheet_id)
					context['sample_data'] = get_sample_info(worksheet_obj)


		## if clear family form submitted
		if 'clear_family_check' in request.POST:
			print(request.POST)
			print('clear family form submitted')
			clear_family_form = ClearFamilyForm(request.POST, worksheet_obj=worksheet_obj)

			if clear_family_form.is_valid():
				cleaned_data = clear_family_form.cleaned_data

				## only perform clearing if box was ticked
				if cleaned_data['clear_family_check']:

					samples = SampleToWorksheet.objects.filter(worksheet=worksheet_obj).order_by('pos')

					for s in samples:
						print(s)
						s.sample.familyid, s.sample.familypos, s.sample.affected = None, None, False
						s.sample.save()

					## reload context
					worksheet_obj = Worksheet.objects.get(worksheet_id = worksheet_id)
					context['sample_data'] = get_sample_info(worksheet_obj)


		## if clinsci sign off pressed
		if 'clinsci_worksheet_checked' in request.POST:

			clinsci_signoff_form = ClinSciSignoffForm(request.POST, worksheet_obj=worksheet_obj)

			if clinsci_signoff_form.is_valid():

				cleaned_data = clinsci_signoff_form.cleaned_data

				# if clinsci manual check tick box is done before clicking 'sign off'
				if cleaned_data['clinsci_worksheet_checked'] == True:

					# all sign off related fields are changed
					worksheet_obj.clinsci_manual_check = True
					worksheet_obj.clinsci_signoff_name = request.user
					worksheet_obj.clinsci_signoff_datetime = datetime.now()
					worksheet_obj.clinsci_signoff_complete = True
					worksheet_obj.save()

					# reload context
					worksheet_obj = Worksheet.objects.get(worksheet_id = worksheet_id)
					context['worksheet_info']['clinsci_signoff_name'] = worksheet_obj.clinsci_signoff_name
					context['worksheet_info']['clinsci_signoff_datetime'] = worksheet_obj.clinsci_signoff_datetime
					context['worksheet_info']['clinsci_signoff_complete'] = worksheet_obj.clinsci_signoff_complete


					# check overall status for clinsci
					clinsci_check_status = Worksheet.get_clinsci_check_status(worksheet_id)
					context['worksheet_checks']['clin_sci']['overall'] = clinsci_check_status['clinsci_checks_overall']
					context['worksheet_checks']['clin_sci']['status_html'] = status_html_lookup[ clinsci_check_status['clinsci_checks_overall'] ]

					# download form. clinsci status has been reloaded so need to see if download is ok now
					if clinsci_check_status['clinsci_checks_overall'] == 'complete' and techteam_check_status['techteam_checks_overall'] == 'complete': 
						download_form = DownloadSamplesheetButton(checks_complete=True)

					else:
						download_form = DownloadSamplesheetButton(checks_complete=False)

					context['download_form'] = download_form


		## if clinsci reopen form is pressed
		if 'clinsci_reopen_check' in request.POST:
			clinsci_open_worksheet = ClinSciOpenWorksheetForm(request.POST, worksheet_obj=worksheet_obj)
			if clinsci_open_worksheet.is_valid():
				cleaned_data = clinsci_open_worksheet.cleaned_data

				if cleaned_data['clinsci_reopen_check'] == True:

					# all sign off related fields are changed back to None/False
					worksheet_obj.clinsci_manual_check = False
					worksheet_obj.clinsci_signoff_name = None
					worksheet_obj.clinsci_signoff_datetime = None
					worksheet_obj.clinsci_signoff_complete = False
					worksheet_obj.save()

					# reload context
					worksheet_obj = Worksheet.objects.get(worksheet_id = worksheet_id)
					context['worksheet_info']['clinsci_signoff_name'] = worksheet_obj.clinsci_signoff_name
					context['worksheet_info']['clinsci_signoff_datetime'] = worksheet_obj.clinsci_signoff_datetime
					context['worksheet_info']['clinsci_signoff_complete'] = worksheet_obj.clinsci_signoff_complete

					# check overall status for clinsci
					clinsci_check_status = Worksheet.get_clinsci_check_status(worksheet_id)
					context['worksheet_checks']['clin_sci']['overall'] = clinsci_check_status['clinsci_checks_overall']
					context['worksheet_checks']['clin_sci']['status_html'] = status_html_lookup[ clinsci_check_status['clinsci_checks_overall'] ]

					# download form. clinsci status has been reloaded so need to see if download is ok now
					if clinsci_check_status['clinsci_checks_overall'] == 'complete' and techteam_check_status['techteam_checks_overall'] == 'complete': 
						download_form = DownloadSamplesheetButton(checks_complete=True)

					else:
						download_form = DownloadSamplesheetButton(checks_complete=False)

					context['download_form'] = download_form


		## if techteam sign off pressed
		if 'techteam_worksheet_checked' in request.POST:

			techteam_signoff_form = TechteamSignoffForm(request.POST, worksheet_obj=worksheet_obj)

			if techteam_signoff_form.is_valid():

				cleaned_data = techteam_signoff_form.cleaned_data

				# if clinsci manual check tick box is done before clicking 'sign off'
				if cleaned_data['techteam_worksheet_checked'] == True:

					# all sign off related fields are changed
					worksheet_obj.techteam_manual_check = True
					worksheet_obj.techteam_signoff_name = request.user
					worksheet_obj.techteam_signoff_datetime = datetime.now()
					worksheet_obj.techteam_signoff_complete = True
					worksheet_obj.save()

					# reload context
					worksheet_obj = Worksheet.objects.get(worksheet_id = worksheet_id)
					context['worksheet_info']['techteam_signoff_name'] = worksheet_obj.techteam_signoff_name
					context['worksheet_info']['techteam_signoff_datetime'] = worksheet_obj.techteam_signoff_datetime
					context['worksheet_info']['techteam_signoff_complete'] = worksheet_obj.techteam_signoff_complete


					# check overall status for clinsci
					techteam_check_status = Worksheet.get_techteam_check_status(worksheet_id)
					context['worksheet_checks']['tech_team']['overall'] = techteam_check_status['techteam_checks_overall']
					context['worksheet_checks']['tech_team']['status_html'] = status_html_lookup[ techteam_check_status['techteam_checks_overall'] ]

					# download form. techteam status has been reloaded so need to see if download is ok now
					if clinsci_check_status['clinsci_checks_overall'] == 'complete' and techteam_check_status['techteam_checks_overall'] == 'complete': 
						download_form = DownloadSamplesheetButton(checks_complete=True)

					else:
						download_form = DownloadSamplesheetButton(checks_complete=False)

					context['download_form'] = download_form


		## if techteam reopen form is pressed
		if 'techteam_reopen_check' in request.POST:
			techteam_open_worksheet = TechteamOpenWorksheetForm(request.POST, worksheet_obj=worksheet_obj)
			if techteam_open_worksheet.is_valid():
				cleaned_data = techteam_open_worksheet.cleaned_data

				if cleaned_data['techteam_reopen_check'] == True:

					# all sign off related fields are changed back to None/False
					worksheet_obj.techteam_manual_check = False
					worksheet_obj.techteam_signoff_name = None
					worksheet_obj.techteam_signoff_datetime = None
					worksheet_obj.techteam_signoff_complete = False
					worksheet_obj.save()

					# reload context
					worksheet_obj = Worksheet.objects.get(worksheet_id = worksheet_id)
					context['worksheet_info']['techteam_signoff_name'] = worksheet_obj.techteam_signoff_name
					context['worksheet_info']['techteam_signoff_datetime'] = worksheet_obj.techteam_signoff_datetime
					context['worksheet_info']['techteam_signoff_complete'] = worksheet_obj.techteam_signoff_complete

					# check overall status for clinsci
					techteam_check_status = Worksheet.get_techteam_check_status(worksheet_id)
					context['worksheet_checks']['tech_team']['overall'] = techteam_check_status['techteam_checks_overall']
					context['worksheet_checks']['tech_team']['status_html'] = status_html_lookup[ techteam_check_status['techteam_checks_overall'] ]

					# download form. techteam status has been reloaded so need to see if download is ok now
					if clinsci_check_status['clinsci_checks_overall'] == 'complete' and techteam_check_status['techteam_checks_overall'] == 'complete': 
						download_form = DownloadSamplesheetButton(checks_complete=True)

					else:
						download_form = DownloadSamplesheetButton(checks_complete=False)

					context['download_form'] = download_form


		## if download samplesheet button is pressed
		if 'download-samplesheet' in request.POST:
			download_button = DownloadSamplesheetButton(request.POST, checks_complete=True)
			if download_button.is_valid():
				cleaned_data = download_button.cleaned_data

				worksheet_list = [worksheet_obj.worksheet_id]
				assay_list = [worksheet_obj.worksheet_test.assay_name]

				## if additional worksheet is selected then put as second worksheet id and assay type
				if cleaned_data['additional_worksheet']:
					print(f'additional worksheet selected: {cleaned_data["additional_worksheet"].worksheet_id}')
					worksheet_obj2 = Worksheet.objects.get(worksheet_id = cleaned_data['additional_worksheet'])
					worksheet_list.append(worksheet_obj2.worksheet_id)
					assay_list.append(worksheet_obj2.worksheet_test.assay_name)

				worksheets = ','.join(worksheet_list)
				assays = ','.join(assay_list)

				# run generate_samplesheet management command and save output as variable
				buffer = StringIO()
				# TODO - add option to reverse complement or not
				call_command('generate_samplesheet', '--worksheets', worksheets, '--assays', assays, stdout=buffer)
				out = buffer.getvalue()
				buffer.close()

				# return csv file for download
				response = HttpResponse(out, content_type='text/csv')
				response['Content-Disposition'] = 'attachment; filename="SampleSheet.csv"'
				return response


	return render(request, 'sample_sheet/worksheet_base.html', context)



## AJAX load of start position for indexes in tech settings form
@transaction.atomic
@login_required
def load_indexes(request):
	print(request)
	index_set = request.GET.get('index_set')
	print(index_set)
	index_list = IndexToIndexSet.objects.filter(index_set=index_set).order_by('pk')
	print(index_list)
	return render(request, 'sample_sheet/startpos_dropdown_list_options.html', {'index_list': index_list})