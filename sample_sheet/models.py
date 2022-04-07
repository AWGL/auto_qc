from django.db import models
import datetime

# Create your models here.
class Assay (models.Model):
	assay_slug = models.CharField(max_length=20, primary_key=True)
	assay_name = models.CharField(max_length=20)
	enable_coupled_worksheets = models.BooleanField(default=False, null=True, blank=True)
	coupled_worksheet_assay = models.OneToOneField('Assay', on_delete=models.SET_NULL, null = True, blank = True)

	def __str__(self):
		return self.assay_name


class Index(models.Model):
    """
    Sequence of an individual index
    """
    #id = models.AutoField(primary_key=True)
    index_name = models.CharField(max_length=20)
    index_well = models.CharField(max_length=5, blank=True, null=True)
    sequence = models.CharField(max_length=20)
    i7_or_i5 = models.CharField(max_length=2)

    class Meta:
        # unique_together = ('index_name', 'i7_or_i5')
        constraints = [
        models.UniqueConstraint(fields=['index_name', 'i7_or_i5'], name='unique_index')]

    def reverse_complement(self):
        "Make reverse complement of index sequence"
        tab = str.maketrans('ATGC', 'TACG')
        return self.sequence.translate(tab)[::-1]

    def __str__(self):
        # return f'{self.index_name}_{self.i7_or_i5}'
        return str(self.index_name)


class IndexSet(models.Model):
    """
    A set of indexes as sold by the vendor
    """

    set_name = models.CharField(max_length=20, primary_key=True)
    vendor = models.CharField(max_length=20, blank=True, null=True)
    product = models.CharField(max_length=20, blank=True, null=True)

    def get_vendor_index_set(self):
        "Get a queryset of all indexes in this set"
        return IndexToIndexSet.objects.filter(index_set=self).order_by('index_pos')

    def __str__(self):
        return self.set_name


class IndexToIndexSet(models.Model):
    """
    Map indexes to vendor index set
    """
    #id = models.AutoField(primary_key=True)
    index1 = models.ForeignKey('Index', on_delete=models.PROTECT, related_name='vendor_index1')
    index2 = models.ForeignKey('Index', on_delete=models.PROTECT, related_name='vendor_index2', blank=True, null=True)
    index_set = models.ForeignKey('IndexSet', on_delete=models.CASCADE)
    index_pos = models.IntegerField()

    def __str__(self):
        return f'{self.index_set}_{self.index1}'


class Sample(models.Model):
    """
    An individual sample from Shire e.g. 20M12345
    This is sample specific but NOT worksheet specific.
    Includes family and affected information
    """
    SEX_CHOICES = [
        ('2', 'Female'),
        ('1', 'Male'),
        ('0', 'Unknown'),
    ]
    FAMILYID_CHOICES = [
        ('','----'),
        ('FAM001', 'FAM001'),
        ('FAM002', 'FAM002'),
        ('FAM003', 'FAM003'),
        ('FAM004', 'FAM004'),
        ('FAM005', 'FAM005'),
        ('FAM006', 'FAM006'),
        ('FAM007', 'FAM007'),
        ('FAM008', 'FAM008'),
        ('FAM009', 'FAM009'),
    ]
    FAMILYPOS_CHOICES = [
        ('Father', 'Father'),
        ('Mother', 'Mother'),
        ('Proband', 'Proband'),
    ]
    sampleid = models.CharField(max_length=20, primary_key=True)
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)
    familyid = models.CharField(max_length=20, choices=FAMILYID_CHOICES, default=None, null=True, blank=True)
    familypos = models.CharField(max_length=20, choices=FAMILYPOS_CHOICES, default=None, null=True, blank=True)
    affected = models.BooleanField(null=True, blank=True, default=False)

    def __str__(self):
        return self.sampleid


 
class Worksheet(models.Model):
    """
    An individual worksheet from Shire e.g. 20-123. Represents a collection of
    samples for a run, a run may be one worksheet or multiple combined worksheets
    """
    SEQ_CHOICES = [
        ('NextSeq', 'NextSeq'),
        ('MiSeq', 'MiSeq'),
        ('HiSeq', 'HiSeq'),
        ('NovaSeq', 'NovaSeq'),
    ]
    
    worksheet_id = models.CharField(max_length=20, primary_key=True)
    worksheet_test = models.ForeignKey('Assay', on_delete=models.PROTECT)
    index_set = models.ForeignKey('IndexSet', on_delete=models.SET_NULL, related_name='worksheet_index_set', blank=True, null=True)
    sequencer = models.CharField(max_length=20, choices=SEQ_CHOICES, default=None, null=True, blank=True)
    clinsci_manual_check = models.BooleanField(default = False)
    clinsci_signoff_name = models.ForeignKey('auth.user', on_delete=models.SET_NULL, related_name='clinsci_user', blank=True, null=True)
    clinsci_signoff_datetime = models.DateTimeField(blank=True, null=True)
    clinsci_signoff_complete = models.BooleanField(default=False)
    techteam_manual_check = models.BooleanField(default = False)
    techteam_signoff_name = models.ForeignKey('auth.user', on_delete=models.SET_NULL, related_name='techteam_user', blank=True, null=True)
    techteam_signoff_datetime = models.DateTimeField(blank=True, null=True)
    techteam_signoff_complete = models.BooleanField(default=False)
    upload_date = models.DateField(null=True, blank=True, default=datetime.date.today)
    worksheet_notes = models.CharField(max_length=200, blank=True, null=True)


    def get_samples_from_ws(self):
        "Get a dictionary of samples in a worksheet, ordered by position"
        samples = SampleToWorksheet.objects.filter(worksheet=self).order_by('pos')

        # format as dict
        sample_dict = {}
        for s in samples:
            sample_dict[str(s.pos)] = {
                'sample': s.sample.sampleid, 
                'referral': s.referral.name,
                'notes' : s.notes,
                'sex': s.sample.get_sex_display(),
                'familyid': s.sample.familyid,
                'familypos': s.sample.familypos,
                'affected': s.sample.affected,
                'index1': s.index1,
                'index2': s.index2,
                'pool': s.pool,
                'sample_obj': s,
                'edited': s.edited
            }
        return sample_dict


    def get_ws_status(self):
        "get status of worksheet, either Incomplete or Signed Off"
        ws_data = Worksheet.objects.get(worksheet_id=self)
        if ws_data.clinsci_manual_check and ws_data.techteam_manual_check:
            status = "Signed Off"
        else:
            status = "Incomplete"
        return status



    def get_techteam_check_status(self):

        ##### autocheck status #####
        # get sample_ws data
        sample_ws_data = SampleToWorksheet.objects.filter(worksheet=self).order_by('pos')

        # set empty lists to append to later
        sampleid_list = []
        indextuple_list = []

        # set defaults for index populated check
        index1_filled = True

        for count, s in enumerate(sample_ws_data):

            if count == 0:
                # set sample id unique to True as default
                sampleid_list.append(s.sample.sampleid)
                sampleid_unique = True

                # set index_unique to True as default
                indextuple_list.append(f'{s.index1}_{s.index2}')
                indextuple_unique = True

            else:
                # if sampleid already in list then change unique to False
                if s.sample.sampleid in sampleid_list:
                    sampleid_unique = False
                else:
                    # if sample not already in samplelist then append
                    sampleid_list.append(s.sample.sampleid)

                # if index tuple already in index list then unique = False. will also fail if no indexes selected
                if f'{s.index1}_{s.index2}' in indextuple_list:
                    indextuple_unique = False
                else:
                    # if index tuple not in list then append to list
                    indextuple_list.append(f'{s.index1}_{s.index2}')

            # if any of index1 not selected then filled = False
            if not s.index1:
                index1_filled = False


        # create dict to return
        techteam_autocheck_dict = {
                        'sampleid_unique' : sampleid_unique,
                        'indextuple_unique': indextuple_unique,
                        'index1_filled' : index1_filled,
                                }

        # default for overall cs checks is complete, changed to error if any false found in dict
        techteam_autochecks_overall = 'complete'

        for key, value in techteam_autocheck_dict.items():
            if not value:
                techteam_autochecks_overall = 'incomplete'



        ##### manualcheck status #####
        # get worksheet data
        worksheet_obj = Worksheet.objects.get(worksheet_id=self)

        # techteam check box and sign off done?
        if worksheet_obj.techteam_manual_check and worksheet_obj.techteam_signoff_complete:
            techteam_manualchecks_overall = 'complete'
        else:
            techteam_manualchecks_overall = 'incomplete'

        # techchecks overall
        if techteam_manualchecks_overall == 'complete' and techteam_autochecks_overall == 'complete':
            techteam_checks_overall = 'complete'
        else:
            techteam_checks_overall = 'incomplete'

        # create dict to output
        techteam_checks_status = {
            'techteam_autochecks_overall' : techteam_autochecks_overall,
            'techteam_manualchecks_overall' : techteam_manualchecks_overall,
            'techteam_checks_overall' : techteam_checks_overall,
        }

        return techteam_checks_status



    def get_clinsci_check_status(self):
        # get sample ws data
        sample_ws_data = SampleToWorksheet.objects.filter(worksheet=self).order_by('pos')

        # get referral type list
        expected_referral_list = list(ReferralType.objects.all().values_list('name', flat = True))
        
        # set empty lists to append to later
        sampleid_list = []

        # set defaults for index populated check
        referral_valid = True

        for count, s in enumerate(sample_ws_data):

            if count == 0:
                # set sample id unique to True as default
                sampleid_list.append(s.sample.sampleid)
                sampleid_unique = True

            else:
                # if sampleid already in list then change unique to False
                if s.sample.sampleid in sampleid_list:
                    sampleid_unique = False
                else:
                    # if sample not already in samplelist then append
                    sampleid_list.append(s.sample.sampleid)

            # if any of referral not in referral list = False
            if str(s.referral) not in expected_referral_list:
                referral_valid = False


        # create dict to return
        clinsci_autocheck_dict = {
                        'sampleid_unique' : sampleid_unique,
                        'referral_valid' : referral_valid,
                                }

        # default for overall cs checks is complete, changed to error if any false found in dict
        clinsci_autochecks_overall = 'complete'

        for key, value in clinsci_autocheck_dict.items():
            if not value:
                clinsci_autochecks_overall = 'error'


        ##### manualcheck status #####
        # get worksheet data
        worksheet_obj = Worksheet.objects.get(worksheet_id=self)

        # clinsci check box and sign off done?
        if worksheet_obj.clinsci_manual_check and worksheet_obj.clinsci_signoff_complete:
            clinsci_manualchecks_overall = 'complete'
        else:
            clinsci_manualchecks_overall = 'incomplete'

        # clinsci overall
        if clinsci_manualchecks_overall == 'complete' and clinsci_autochecks_overall == 'complete':
            clinsci_checks_overall = 'complete'
        else:
            clinsci_checks_overall = 'incomplete'

        # create dict to output
        clinsci_checks_status = {
            'clinsci_autochecks_overall' : clinsci_autochecks_overall,
            'clinsci_manualchecks_overall' : clinsci_manualchecks_overall,
            'clinsci_checks_overall' : clinsci_checks_overall,
        }

        return clinsci_checks_status

    def dropdown_str(self):
        return f'{self.worksheet_id}_test'

    def __str__(self):
        return self.worksheet_id



class ReferralType(models.Model):
    """
    A referral type from Shire
    """
    # code = models.CharField(max_length=6
    name = models.CharField(max_length=20, primary_key=True)
    shire_name = models.CharField(max_length=50, null=True, blank=True)
    assay = models.ManyToManyField('Assay')

    def __str__(self):
        return self.name


class SampleToWorksheet(models.Model):
    """
    Map samples onto worksheets.
    this is sample AND worksheet specific
    """
    POOL_CHOICES = [
        ('Y', 'Include in pool'),
        ('N1', 'Not in pool - skip index'),
        ('N2', 'Not in pool - include index'),
    ]
    sample = models.ForeignKey('Sample', on_delete=models.PROTECT) # TODO related name
    worksheet = models.ForeignKey('Worksheet', on_delete=models.CASCADE) # TODO related name
    referral = models.ForeignKey('ReferralType', on_delete=models.PROTECT, default='null') #, related_name='custom_index1'
    pos = models.IntegerField()
    index1 = models.ForeignKey('Index', on_delete=models.PROTECT, related_name='sample_index1', blank=True, null=True)
    index2 = models.ForeignKey('Index', on_delete=models.PROTECT, related_name='sample_index2', blank=True, null=True)
    pool = models.CharField(max_length=2, choices=POOL_CHOICES, default='Y')
    edited = models.BooleanField(default=False)
    notes = models.CharField(max_length=200, blank=True, null=True)


    # TODO - index? will allow for tweaking the indexes if e.g theres an accidental swap
    def reload_skipped_indexes(self):
        return None

    def __str__(self):
        return f'{self.pos}_{self.worksheet}_{self.sample}'