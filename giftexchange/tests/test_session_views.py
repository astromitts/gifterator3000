from django.urls import reverse

from giftexchange.tests.helpers import TestBase


class SessionViewTestCase(TestBase):

	def setUp(self):
		super(SessionViewTestCase, self).setUp()
		self.register_url = reverse('register')
		self.login_url = reverse('login')
		self.dashboard_url = reverse('dashboard')

	def _register(self, post_data):
		result = self.client.post(self.register_url, post_data, follow=True)
		return result

class TestRegisterView(SessionViewTestCase):
	def test_user_register_password_must_match(self):
		register_post_data = {
			'email': 'testemail@example.com',
			'first_name': 'Tester',
			'last_name': 'User',
			'password': 'password123',
			'confirm_password': 'password456'
		}
		result = self._register(register_post_data)
		self.assertMessages(result, [('error', 'Password fields must match'), ])
		self.assertEqual(self.register_url, result.request['PATH_INFO'])

	def test_user_register_and_login_success(self):
		register_post_data = {
			'email': 'testemail@example.com',
			'first_name': 'Tester',
			'last_name': 'User',
			'password': 'password123',
			'confirm_password': 'password123'
		}
		result = self._register(register_post_data)
		self.assertMessages(result, [('success', 'You registered to Gifterator 3000! Please login to continue!'), ])
		self.assertEqual(self.login_url, result.request['PATH_INFO'])

		login_post_data = {
			'email': register_post_data['email'],
			'password': register_post_data['password']
		}
		result = self.client.post(self.login_url, login_post_data, follow=True)
		self.assertEqual(self.dashboard_url, result.request['PATH_INFO'])

	def test_email_already_exists(self):
		register_post_data = {
			'email': 'testemail@example.com',
			'first_name': 'Tester',
			'last_name': 'User',
			'password': 'password123',
			'confirm_password': 'password123'
		}
		self._register(register_post_data)
		result = self._register(register_post_data)
		self.assertMessages(result, [('error', 'A user with this email address already exists'), ])
		self.assertEqual(self.register_url, result.request['PATH_INFO'])

