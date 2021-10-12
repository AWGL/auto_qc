import unittest

from qc_database.utils.relatedness2 import relatedness_test

class TestRelatedness(unittest.TestCase):

	def test_function_with_one_family(self):
		result, comment = relatedness_test('qc_database/tests/test_data/210622_A00748_0110_AH5T3CDRXY.ped', 'qc_database/tests/test_data/210622_A00748_0110_AH5T3CDRXY.relatedness2', 0.2, 0.06, 0.06, 0.4)
		self.assertEqual(result, True)

	def test_ped_with_parent_not_related(self):
		result, comment = relatedness_test('qc_database/tests/test_data/210622_A00748_0110_AH5T3CDRXY.ped', 'qc_database/tests/test_data/210622_A00748_0110_AH5T3CDRXYFAIL.relatedness2', 0.2, 0.06, 0.06, 0.4)
		self.assertEqual(result, False)

	def test_parents_related(self):
		result, comment = relatedness_test('qc_database/tests/test_data/210622_A00748_0110_AH5T3CDRXY.ped', 'qc_database/tests/test_data/210622_A00748_0110_AH5T3CDRXYPR.relatedness2', 0.2, 0.06, 0.06, 0.4)
		self.assertEqual(result, False)

	def test_function_with_multiple_families(self):
		result, comment = relatedness_test('qc_database/tests/test_data/201215_A00748_0068_AHT3FCDMXX.ped', 'qc_database/tests/test_data/201215_A00748_0068_AHT3FCDMXX.relatedness2', 0.2, 0.06, 0.06, 0.4)
		self.assertEqual(result, True)

	def test_either_ped_or_relatedness_file_not_found(self):
		result, comment = relatedness_test('this_file_does_not_exist.ped', 'this_file_also_does_not_exist.relatedness2', 0.2, 0.06, 0.06, 0.4)
		self.assertEqual(result, False)

	def test_tso_no_one_related(self):

		# should not fail as no one related
		result, comment = relatedness_test('qc_database/tests/test_data/210709_NB551319_0232_AHF2JFBGXJ.ped', 'qc_database/tests/test_data/210709_NB551319_0232_AHF2JFBGXJ.relatedness2', 0.2, 0.06, 0.06, 0.4)

		self.assertEqual(result, True)

	def test_tso_no_one_related_unexpected_related(self):

		# relatedness between 18M01316	21M11357 is 0.2
		result, comment = relatedness_test('qc_database/tests/test_data/210709_NB551319_0232_AHF2JFBGXJ.ped', 'qc_database/tests/test_data/210709_NB551319_0232_AHF2JFBGXJ_2.relatedness2', 0.2, 0.06, 0.06, 0.4)

		self.assertEqual(result, False)

	def test_big_genome_run(self):

		# Test run with 5 correct trios
		result, comment = relatedness_test('qc_database/tests/test_data/K00150_0149_AHG7YKBBXX.ped', 'qc_database/tests/test_data/K00150_0149_AHG7YKBBXX.relatedness2', 0.2, 0.06, 0.06, 0.4)

		print (result, comment)
		self.assertEqual(result, True,msg=[result, comment])

	def test_duplicate_sample1(self):

		# test correct wings run with same sample repeated

		result, comment = relatedness_test('qc_database/tests/test_data/210604_A00748_0108_AHWVTGDMXX.ped', 'qc_database/tests/test_data/210604_A00748_0108_AHWVTGDMXX.relatedness2', 0.2, 0.06, 0.06, 0.4)
		self.assertEqual(result, False)

	def test_tso_no_one_related_unexpected_related_duplicate(self):

		# relatedness a duplicate sample - 18M01316	21M10702
		result, comment = relatedness_test('qc_database/tests/test_data/210709_NB551319_0232_AHF2JFBGXJ.ped', 'qc_database/tests/test_data/210709_NB551319_0232_AHF2JFBGXJ_duplicate.relatedness2', 0.2, 0.06, 0.06, 0.4)
		self.assertEqual(result, False)

	def test_multiple_trios_fail(self):

		# should fail as 19M06442 is not related to its dad 20M11003
		result, comment = relatedness_test('qc_database/tests/test_data/201215_A00748_0068_AHT3FCDMXX_2.ped', 'qc_database/tests/test_data/201215_A00748_0068_AHT3FCDMXX_2.relatedness2', 0.2, 0.06, 0.06, 0.4)

		self.assertEqual(result, False)

	def test_multiple_trios_fail2(self):

		# should fail as 19M06442 is a duplicate of its dad 20M11003
		result, comment = relatedness_test('qc_database/tests/test_data/201215_A00748_0068_AHT3FCDMXX_2.ped', 'qc_database/tests/test_data/201215_A00748_0068_AHT3FCDMXX_3.relatedness2', 0.2, 0.06, 0.06, 0.4)

		self.assertEqual(result, False)

	def test_mixed_up_relatedness_mum_not_in_same_family(self):

		# should fail as 20M08216 (FAM001) is not in same family as mum (20M11351)
		result, comment = relatedness_test('qc_database/tests/test_data/201215_A00748_0068_AHT3FCDMXX_4.ped', 'qc_database/tests/test_data/201215_A00748_0068_AHT3FCDMXX.relatedness2', 0.2, 0.06, 0.06, 0.4)

		self.assertEqual(result, False)

	def test_siblings(self):

		# should fail as 20M08216 (FAM001) is not in same family as mum (20M11351)
		result, comment = relatedness_test('qc_database/tests/test_data/siblings.ped', 'qc_database/tests/test_data/siblings.relatedness2', 0.2, 0.06, 0.06, 0.4)

		self.assertEqual(result, True)


	def test_no_parent_in_relatedness_file(self):

		# should fail as 20M08216 (FAM001) is not in same family as mum (20M11351)
		result, comment = relatedness_test('qc_database/tests/test_data/wrong_ped_no_parents.ped', 'qc_database/tests/test_data/wrong_ped_no_parents.relatedness2', 0.2, 0.06, 0.06, 0.4)

		self.assertEqual(result, False)

if __name__ == '__main__':
	unittest.main()

