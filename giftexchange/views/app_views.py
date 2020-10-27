from datetime import date
from django.contrib import messages
from django.template import loader
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.models import User
from django.views import View

from giftexchange.views.base_views import (
	AuthenticatedView,
	BaseView,
	GiftExchangeView,
)

from giftexchange.forms import (
	ParticipantDetailsForm,
	GiftExchangeCreateForm,
	FileUploadForm,
	ProfileForm,
	GiftForm,
)
from giftexchange.models import Participant, AppUser, GiftExchange, AppInvitation


class ManageProfile(AuthenticatedView):
	def setup(self, request, *args, **kwargs):
		super(ManageProfile, self).setup(request, *args, **kwargs)
		self.template = loader.get_template('giftexchange/profile.html')
		self.context = {
			'breadcrumbs': [
				('Profile', None)
			],
			'fullwidth': True
		}

	def get(self, request, *args, **kwargs):
		init = {
			'first_name': self.djangouser.first_name,
			'last_name': self.djangouser.last_name,
			'email': self.djangouser.email,
			'default_likes': self.appuser.default_likes,
			'default_dislikes': self.appuser.default_dislikes,
			'default_allergies_and_sensitivites': self.appuser.default_allergies_sensitivities,
			'default_shipping_address': self.appuser.default_shipping_address
		}
		self.context['form'] = ProfileForm(initial=init)
		return HttpResponse(self.template.render(self.context, request))

	def post(self, request, *args, **kwargs):
		form = ProfileForm(request.POST)
		if form.is_valid:
			self.djangouser.email = request.POST['email']
			self.djangouser.first_name = request.POST['first_name']
			self.djangouser.last_name = request.POST['last_name']
			self.djangouser.save()
			self.appuser.default_likes = request.POST['default_likes']
			self.appuser.default_dislikes = request.POST['default_dislikes']
			self.appuser.default_allergies_sensitivities = request.POST['default_allergies_and_sensitivites']
			self.appuser.default_shipping_address = request.POST['default_shipping_address']
			self.appuser.save()

			messages.success(request, 'Updated user profile information')
			return redirect(reverse('profile'))
		else:
			self.context['form'] = form
			return HttpResponse(self.template.render(self.context, request))


class Dashboard(AuthenticatedView):
	""" Home page
		Lists all current gift exchanges that a user is participating in
		Has link to create a new gift exchange
	"""
	def get(self, request, *args, **kwargs):
		template = loader.get_template('giftexchange/dashboard.html')
		today = date.today()
		current_participation = Participant.objects.filter(appuser=self.appuser, status='active')
		pending_participation = Participant.objects.filter(appuser=self.appuser, status='invited')
		current_exchanges = []
		pending_exchanges = []
		past_exchanges = []

		for cp in current_participation:
			if cp.giftexchange.date >= today:
				current_exchanges.append(cp.giftexchange)
			else:
				past_exchanges.append(cp.giftexchange)

		for cp in pending_participation:
			if cp.giftexchange.date >= today and not cp.giftexchange.assignments_locked:
				pending_exchanges.append(cp.giftexchange)

		context = {
			'breadcrumbs': [],
			'current_exchanges': current_exchanges,
			'invitations': pending_exchanges,
			'past_exchanges': past_exchanges,
			'appuser': self.appuser,
		}

		return HttpResponse(template.render(context, request))


class AcceptGiftExchangeInvitation(AuthenticatedView):
	def get(self, request, *args, **kwargs):
		giftexchange, participant_details = self._get_participant_and_exchange(self.appuser, self.giftexchange_id)
		participant_details.status = 'active'
		participant_details.save()
		participant_details.update(
			likes=self.appuser.default_likes,
			dislikes=self.appuser.default_dislikes,
			allergies_sensitivities=self.appuser.default_allergies_sensitivities
		)
		messages.success(request, 'You have been added to "{}"'.format(self.giftexchange.title))
		return redirect(reverse('dashboard'))


class DeclineGiftExchangeInvitation(AuthenticatedView):
	def get(self, request, *args, **kwargs):
		giftexchange, participant_details = self._get_participant_and_exchange(self.appuser, self.giftexchange_id)
		participant_details.status = 'declined'
		participant_details.save()
		messages.success(request, 'You have declined "{}"'.format(self.giftexchange.title))
		return redirect(reverse('dashboard'))


class CreateGiftExchange(AuthenticatedView):
	""" View to handle creating a new gift exchange
	"""
	def setup(self, request, *args, **kwargs):
		super(CreateGiftExchange, self).setup(request, *args, **kwargs)
		self.context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				('Create A Gift Exchange', None)
			],
			'form': None,
		}
		self.template = loader.get_template('giftexchange/generic_form.html')

	def post(self, request, *args, **kwargs):
		form = GiftExchangeCreateForm(request.POST)
		if form.is_valid():
			giftexchange = GiftExchange.create(
				title=request.POST['title'],
				description=request.POST['description'],
				spending_limit=request.POST['spending_limit'],
				location=request.POST['location'],
				date=request.POST['date'],
				appuser=self.appuser
			)
			return redirect(reverse('dashboard'))
		else:
			self.context['form'] = form
			return HttpResponse(self.template.render(self.context, request))

	def get(self, request, *args, **kwargs):
		self.context['form'] = GiftExchangeCreateForm()
		return HttpResponse(self.template.render(self.context, request))


class GiftExchangePersonalDetail(GiftExchangeView):
	""" Display page for your details on a gift exchange
	"""
	def get(self, request, *args, **kwargs):
		if not kwargs.get('appuser_id'):
			appuser = AppUser.get(djangouser=request.user)
			giftexchange, participant_details = self._get_participant_and_exchange(appuser, self.giftexchange_id)
			breadcrumbs = [
				('dashboard', reverse('dashboard')),
				(self.giftexchange.title, None)
			]
		else:
			if not self.is_admin:
				return Http404('User not an admin on this exchange')

			appuser = AppUser.objects.get(pk=kwargs.get('appuser_id'))
			giftexchange, participant_details = self._get_participant_and_exchange(appuser, self.giftexchange_id)
			breadcrumbs = [
				('dashboard', reverse('dashboard')),
				(self.giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Admin', reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Manage Assignments', reverse('giftexchange_manage_assignments', kwargs={'giftexchange_id': self.giftexchange_id})),
				('{} {}'.format(appuser.djangouser.first_name, appuser.djangouser.last_name), None)
			]

		assignment_details = None
		if self.giftexchange.assignments_locked:
			assignment_details = giftexchange.get_assignment(appuser)


		template = loader.get_template('giftexchange/giftexchange_detail.html')
		context = {
			'breadcrumbs': breadcrumbs,
			'admin_user': self.is_admin,
			'appuser': appuser,
			'participant_details': participant_details,
			'assignment_details': assignment_details,
			'giftexchange': giftexchange
		}
		return HttpResponse(template.render(context, request))


class GiftExchangeDetailResult(GiftExchangeView):
	""" Display page for your details on a gift exchange
	"""
	def get(self, request, *args, **kwargs):
		my_giver = self.giftexchange.get_giver(self.appuser)
		participant_details = self.giftexchange.get_participant(self.appuser)
		assignments = self.giftexchange.ordered_assignments
		template = loader.get_template('giftexchange/giftexchange_results.html')
		context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				('{} Results'.format(self.giftexchange.title), None)
			],
			'admin_user': self.is_admin,
			'appuser': self.appuser,
			'my_giver': my_giver,
			'assignments': assignments,
			'giftexchange': self.giftexchange,
			'participant_details': participant_details,
		}
		return HttpResponse(template.render(context, request))


class GiftExchangeSetGift(GiftExchangeView):
	def setup(self, request, *args, **kwargs):
		super(GiftExchangeSetGift, self).setup(request, *args, **kwargs)
		self.return_url = reverse('giftexchange_detail_review', kwargs={'giftexchange_id': self.giftexchange.id})
		if kwargs.get('appuser_id'):
			self.appuser = AppUser.objects.get(pk=kwargs['appuser_id'])
			breadcrumbs = [
				('dashboard', reverse('dashboard')),
				('{} Results'.format(self.giftexchange.title), self.return_url),
				('Update Gift for {} {}'.format(self.appuser.djangouser.first_name, self.appuser.djangouser.last_name), None)
			]
		else:
			breadcrumbs = [
				('dashboard', reverse('dashboard')),
				('{} Results'.format(self.giftexchange.title), self.return_url),
				('Update Gift', None)
			]

		self.template = loader.get_template('giftexchange/generic_form.html')
		self.participant_details = self.giftexchange.get_participant(self.appuser)
		self.context = {
			'breadcrumbs': breadcrumbs,
			'form': None,
		}

	def get(self, request, *args, **kwargs):
		self.context['form'] = GiftForm(instance=self.participant_details)
		return HttpResponse(self.template.render(self.context, request))

	def post(self, request, *args, **kwargs):
		form = GiftForm(request.POST)
		if form.is_valid:
			self.participant_details.set_gift(request.POST['gift'])
			messages.success(request, 'Gift updated, thanks!')
			return redirect(self.return_url)
		else:
			self.context['form'] = form
			return HttpResponse(self.template.render(self.context, request))



class GiftExchangePersonalDetailEdit(GiftExchangeView):
	""" View to handle updating the participant details of a gift exchange
		e.g., likes, dislikes, etc
	"""
	def setup(self, request, *args, **kwargs):
		super(GiftExchangePersonalDetailEdit, self).setup(request, *args, **kwargs)
		self.template = loader.get_template('giftexchange/generic_form.html')
		self.context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				(self.giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Edit My Details', None),
			],
			'form': None,
		}

	def post(self, request, *args, **kwargs):
		form = ParticipantDetailsForm(request.POST)
		if form.is_valid():
			self.participant_details.update(
				likes=request.POST['likes'],
				dislikes=request.POST['dislikes'],
				allergies_sensitivities=request.POST['allergies_sensitivities'],
				shipping_address=request.POST['shipping_address']
			)
			messages.success(request, 'Updated your details for this gift exchange')
			return redirect(reverse('giftexchange_detail', kwargs={'giftexchange_id': self.giftexchange_id}))
		else:
			form = ParticipantDetailsForm(instance=self.participant_details)
			self.context['form'] = form
			return HttpResponse(self.template.render(self.context, request))

	def get(self, request, *args, **kwargs):
		form = ParticipantDetailsForm(instance=self.participant_details)
		self.context['form'] = form
		return HttpResponse(self.template.render(self.context, request))
