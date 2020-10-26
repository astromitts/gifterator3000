from django.test import TestCase
from django.test import Client


class TestBase(TestCase):
	def setUp(self):
		self.client = Client(enforce_csrf_checks=False)

	def assertMessages(self, client_result, expected_messages):
		context_messages = list(client_result.context['messages'])
		messages = [(cm.level_tag, cm.message) for cm in context_messages]
		self.assertEqual(expected_messages, messages)
