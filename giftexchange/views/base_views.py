from urllib.parse import urlparse
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.contrib.auth.views import redirect_to_login
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, resolve_url
from django.views import View
from django.urls import reverse



from giftexchange.models import AppUser, GiftExchange, Participant


class UnAuthenticatedView(View):
	def get(self, request, *args, **kwargs):
		if request.user.is_authenticated:
			messages.warning(request, 'You are already logged in here.')
			return redirect(reverse('dashboard'))


class BaseView(View):
	""" Base view class to hold commonly required utils
	"""
	def _get_participant_and_exchange(self, appuser, giftexchange_id):
		giftexchange = None
		participant_details = None

		giftexchange = GiftExchange.objects.filter(pk=giftexchange_id).first()

		if giftexchange:
			participant_details = Participant.objects.filter(giftexchange=giftexchange, email=appuser.djangouser.email)
		return giftexchange, participant_details

	def _full_url_reverse(self, request, url_name):
		return '{}://{}{}'.format(request.scheme, request.get_host(), reverse(url_name))


class AuthenticatedView(BaseView):
	""" Base class thay boots you from a view if you are not logged in
		also does some other variable assignments that are commonly required

		Wow LoginRequiredMixin was not working at all so I had to copy a bunch of it here :\
	"""
	login_url = '/login/'
	permission_denied_message = 'Login required'
	raise_exception = False
	redirect_field_name = REDIRECT_FIELD_NAME

	def get_login_url(self):
		"""
		Override this method to override the login_url attribute.
		"""
		login_url = self.login_url or settings.LOGIN_URL
		if not login_url:
			raise ImproperlyConfigured(
				'{0} is missing the login_url attribute. Define {0}.login_url, settings.LOGIN_URL, or override '
				'{0}.get_login_url().'.format(self.__class__.__name__)
			)
		return str(login_url)


	def get_redirect_field_name(self):
		"""
		Override this method to override the redirect_field_name attribute.
		"""
		return self.redirect_field_name

	def handle_no_permission(self):
		if self.raise_exception or self.request.user.is_authenticated:
			raise PermissionDenied(self.get_permission_denied_message())

		path = self.request.build_absolute_uri()
		resolved_login_url = resolve_url(self.get_login_url())
		# If the login url is the same scheme and net location then use the
		# path as the "next" url.
		login_scheme, login_netloc = urlparse(resolved_login_url)[:2]
		current_scheme, current_netloc = urlparse(path)[:2]
		if (
			(not login_scheme or login_scheme == current_scheme) and
			(not login_netloc or login_netloc == current_netloc)
		):
			path = self.request.get_full_path()
			return redirect_to_login(
				path,
				resolved_login_url,
				self.get_redirect_field_name(),
			)

	def dispatch(self, request, *args, **kwargs):
		if not request.user.is_authenticated:
			return self.handle_no_permission()
		return super().dispatch(request, *args, **kwargs)

	def setup(self, request, *args, **kwargs):
		super(AuthenticatedView, self).setup(request, *args, **kwargs)

		if not request.user.is_authenticated:
			return self.handle_no_permission()

		self.giftexchange = None
		self.is_admin = False
		self.djangouser = request.user
		self.appuser = AppUser.get(djangouser=self.djangouser)
		if 'giftexchange_id' in kwargs:
			self.giftexchange = GiftExchange.objects.filter(pk=kwargs['giftexchange_id']).first()
			self.giftexchange_id = self.giftexchange.pk


class GiftExchangeView(AuthenticatedView):
	""" Base authenticated class that specifically validates that a given user
		has permission to be on a page for a specific gift page
	"""
	def setup(self, request, *args, **kwargs):
		super(GiftExchangeView, self).setup(request, *args, **kwargs)
		if not self.giftexchange:
			return Http404('Gift exchange not found')
		else:
			self.participant_details = self.appuser.exchange_participant(self.giftexchange)
		if self.giftexchange:
			self.is_admin = self.appuser in self.giftexchange.admin_appuser.all()


class GiftExchangeAdminView(AuthenticatedView):
	""" Authenticated view that allows only users who have admin access to a gift exchange
	"""
	def setup(self, request, *args, **kwargs):
		super(GiftExchangeAdminView, self).setup(request, *args, **kwargs)
		self.giftexchange_id = kwargs['giftexchange_id']
		self.appuser = AppUser.get(djangouser=request.user)
		self.giftexchange, self.participant_details = self._get_participant_and_exchange(self.appuser, self.giftexchange_id)

		if not self.giftexchange:
			raise Http404('Gift exchange with id {} not found'.format(self.giftexchange_id))
		if not self.appuser in self.giftexchange.admin_appuser.all():
			raise Http404('User not an admin on this exchange')


class ParticipantAdminAction(GiftExchangeAdminView):
	""" Base view for gift exchange admin pages that target a specific participant
	"""
	def setup(self, request, *args, **kwargs):
		super(ParticipantAdminAction, self).setup(request, *args, **kwargs)
		self.target_participant = Participant.objects.get(pk=kwargs['participant_id'])
		self.return_url = reverse('giftexchange_manage_participants', kwargs={'giftexchange_id': self.giftexchange_id})
