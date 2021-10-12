#!/usr/bin/env python

import pandas as pd
import csv

"""
relatedness.py

Calculates whether the relationships between proband and parents are what is expected

"""

def get_relatedness(df, sample1, sample2):
	"""
	Given a df on the relatedness2 file return the relatedness value
	
	df (pd.DataFrame): Pandas dataframe of relatedness2 file
	sample1 (str): A sample id
	sample2 (str): A sample id
	
	Returns float or None
	"""
	rows = df[(df['INDV1'] == sample1) & (df['INDV2'] == sample2)]
	
	if rows.shape[0] == 0:
		
		return None
	
	else:
		
		return rows['RELATEDNESS_PHI'].iloc[0]
	
def check_relatedness_parent(df, sample_id, parent_id, min_relatedness_parents, max_relatedness_parents):
	"""
	Check the relatedness between a parents of a sample.
	
	df (pd.DataFrame): Pandas dataframe of relatedness2 file
	sample_id (str): Proband id
	parent_id (str): The parent id
	min_relatedness_parents (float): See relatedness_test
	max_relatedness_parents (float): See relatedness_test
	
	Return True if the relatedness is not between min_relatedness_parents and max_relatedness_parents
	
	"""
	
	# ignore if parent is undefined
	if parent_id not in [0, '0']:
		
		relatedness_parent = get_relatedness(df, sample_id, parent_id)

		if relatedness_parent is None:

			return False

		else:

			# check between min and max relatedness
			if not min_relatedness_parents <= relatedness_parent <= max_relatedness_parents:

				return True
			
			
	return False

def get_family_and_sample_dicts(ped):
	"""
	Parse the ped file and create two diction
	
	ped (str): Path to PED file
	
	Returns two dictionaries
	"""

	sample_dict = {}
	
	family_dict = {'singletons': []}
	
	# open ped
	with open(ped) as csvfile:
		
		spamreader = csv.reader(csvfile, delimiter='\t')
		
		# loop through each row
		for row in spamreader:
			
			fam_id = row[0]
			sample_id = row[1]
			dad_id = row[2]
			mum_id = row[3]
			
			# make family dict which links samples to a family
			if fam_id == 0 or fam_id == '0':
				
				family_dict['singletons'].append(sample_id)
			
			else:
				
				if fam_id not in family_dict:
					
					family_dict[fam_id] = [sample_id]
					
				else:
					
					family_dict[fam_id].append(sample_id)
					
					
			# create sample dict which links samples to relatives
			if sample_id in sample_dict:
				
				raise Exception('Duplicate sample in PED file.')
			
			sample_dict[sample_id] = {'mum': mum_id, 'dad': dad_id, 'family_id': fam_id}

			
	return sample_dict, family_dict

def relatedness_test(ped, relatedness_file, min_relatedness_parents, max_relatedness_unrelated, max_relatedness_between_parents, max_child_parent_relatedness):
	"""
	Completes a relatedness test given a ped file and a relatedness2 file.
	
	Checks for:
	
	1) All samples with parents have a relatedness between min_relatedness_parents and max_child_parent_relatedness
	2) No unrelated samples have a relatedness larger than max_relatedness_unrelated
	3) No parents have a relatedness larger than max_relatedness_between_parents
	
	ped (str): Path to ped file
	relatedness_file (str): Path to relatedness2 file
	min_relatedness_parents (float): A child and their parent must have a higher relatedness than this value
	max_relatedness_unrelated (float): Two unrelated samples cannot have a higher relatedness than this value
	max_relatedness_between_parents (float): Parents of a sample should not have higher relatedness than this value
	max_child_parent_relatedness (float): A sample should not be related to their parent by more than this value
	
	returns a tuple (Boolean, list)
	
	where the list contains strings describing what went wrong and the boolean = True for pass, False for fail
	"""
	
	fails = []
	
	# Try opening the ped file
	try:
		
		relatedness_df = pd.read_csv(relatedness_file, delimiter = '\t')
		
	except:
		
		fails.append('The relatedness file could not be found.')
	
	# now create a dictionary with each sample as a key
	try:
		
		sample_dict, family_dict =  get_family_and_sample_dicts(ped)
		
	except:
		
		fails.append('The pedigree file could not be parsed.')
		return False, fails
		
	for sample_id in sample_dict:
		
		# check sample is related to their parent (if they have one)
		fam_id = sample_dict[sample_id]['family_id'] 
		mum_id = sample_dict[sample_id]['mum'] 
		dad_id = sample_dict[sample_id]['dad']
		
		same_family = family_dict.get(fam_id, [])
		
		# check sample is related to parents
		for parent_id in [mum_id, dad_id]:
			
			relatedness_status = check_relatedness_parent(relatedness_df, sample_id, parent_id, min_relatedness_parents, max_child_parent_relatedness )
			
			if relatedness_status:
				
				fails.append(f'sample {sample_id} invalid relatedness to parent {parent_id}.')

			#check parent is not a sample not in relatedness
			if parent_id not in same_family and same_family is not False and parent_id not in [0,'0']:

				fails.append(f'sample {sample_id} invalid relatedness to parent {parent_id}.')
				
		# check for duplicate samples i.e. samples not in same family which have > max_relatedness_unrelated
		for other_sample in sample_dict:

			if other_sample not in same_family and other_sample != sample_id:
							
				other_sample_relatedness = get_relatedness(relatedness_df, sample_id, other_sample)

				if other_sample_relatedness is not None:
				
					if other_sample_relatedness > max_relatedness_unrelated:
					
						fails.append(f'{sample_id} is related to non family member {other_sample}')

				else:

					fails.append(f'Could not retrieve relatedness between {sample_id} and {other_sample}')
		
		# check parents are not related
		relatedness_parents = get_relatedness(relatedness_df, mum_id, dad_id)
		
		if relatedness_parents is not None:
			
			if relatedness_parents > max_relatedness_between_parents:
				
				fails.append(f'{sample_id} parents are related to each other.')
	
	# if fails list in empty  then no issues	
	if not fails:
		
		return True, ['No relatedness errors.']
	
	else:
		
		return False, fails

if __name__ == '__main__':

	ped = '/media/joseph/Storage/data/dragen_results/200327_A00748_0019_AHL3JHDRXX/NexteraDNAFlex/post_processing/results/ped/200327_A00748_0019_AHL3JHDRXX.ped'
	relatedness2 = '/media/joseph/Storage/data/dragen_results/200327_A00748_0019_AHL3JHDRXX/NexteraDNAFlex/post_processing/results/relatedness/200327_A00748_0019_AHL3JHDRXX.relatedness2'

	min_relatedness_parents = 0.2
	max_relatedness_unrelated = 0.06
	max_relatedness_between_parents = 0.06
	max_child_parent_relatedness = 0.4

	result = relatedness_test(ped, relatedness2, min_relatedness_parents, max_relatedness_unrelated, max_relatedness_between_parents, max_child_parent_relatedness  )
	print(result)






