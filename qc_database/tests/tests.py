from django.test import TestCase
from acmg_db.models import *

class TestAutoQC(TestCase):
	"""
	Simple tests to check we get right response code from a view
	"""

	fixtures = []

	def setUp(self):

		self.client.login(username='admin', password= 'hello123')