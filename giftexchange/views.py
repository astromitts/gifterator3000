from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.template import loader
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.models import User
from django.views import View

from giftexchange.forms import (
	ParticipantDetailsForm, 
	GiftExchangeDetailsForm, 
	LoginForm, 
	GiftExchangeCreateForm,
	FileUploadForm,
	ProfileForm,
	PasswordResetForm,
)
from giftexchange.models import Participant, AppUser, GiftExchange
from giftexchange.utils import csv_lines_to_dict, save_parsed_participants_as_appusers

import csv


class LoginHandler(View):
	def setup(self, request, *args, **kwargs):
		super(LoginHandler, self).setup(request, *args, **kwargs)
		self.template = loader.get_template('giftexchange/generic_form.html')
		self.context = {}

	def get(self, request, *args, **kwargs):
		if request.user.is_authenticated:
			messages.info(request, 'You are already logged in')
			return redirect(reverse('dashboard'))
		self.context['form'] = LoginForm()
		return HttpResponse(self.template.render(self.context, request))

	def post(self, request, *args, **kwargs):
		data = request.POST.copy()
		form = LoginForm(data)
		if form.is_valid():
			try:
				user = User.objects.get(email=data['email'])
				if user.check_password(data['password']):
					login(request, user)
					return redirect(reverse('dashboard'))
				else: 
					context = {
						'form': form
					}
					messages.error(request, 'Invalid password.')
					return HttpResponse(self.template.render(context, request))
			except Exception as exc:
				context = {
					'form': form
				}
				messages.error(request, 'Invalid email.')
				return HttpResponse(self.template.render(context, request))
		else:
			self.context['form'] = form
			return HttpResponse(self.template.render(self.context, request))


def logout_handler(request):
    logout(request)
    return redirect(reverse('login'))


class BaseView(View):
	""" Base view class to hold commonly required utils
	"""
	def _get_participant_and_exchange(self, appuser, giftexchange_id):
		giftexchange = None
		participant_details = None

		giftexchange = GiftExchange.objects.filter(pk=giftexchange_id).first()
		
		if giftexchange:
			participant_details = appuser.exchange_participant(giftexchange)
		return giftexchange, participant_details


class AuthenticatedView(BaseView):
	""" Base class thay boots you from a view if you are not logged in
		also does some other variable assignments that are commonly required
	"""
	def setup(self, request, *args, **kwargs):
		super(AuthenticatedView, self).setup(request, *args, **kwargs)
		if not self.request.user.is_authenticated:
			raise Http404('Login Required')

		self.giftexchange = None
		self.is_admin = False
		self.djangouser = request.user
		self.appuser = AppUser.get(djangouser=self.djangouser)

		if 'giftexchange_id' in kwargs:
			self.giftexchange = GiftExchange.objects.filter(pk=kwargs['giftexchange_id']).first()
			self.giftexchange_id = self.giftexchange.pk


class UpdatePassword(AuthenticatedView):
	def setup(self, request, *args, **kwargs):
		super(UpdatePassword, self).setup(request, *args, **kwargs)
		self.template = loader.get_template('giftexchange/generic_form.html')
		self.context = {}

	def get(self, request, *args, **kwargs):
		self.context['form'] = PasswordResetForm()
		return HttpResponse(self.template.render(self.context, request))

	def post(self, request, *args, **kwargs):
		data = request.POST.copy()
		form = PasswordResetForm(data)
		if form.is_valid():
			if request.user.check_password(data['current_password']):
				if request.POST['new_password'] == request.POST['confirm_new_password']:
					self.djangouser.set_password(request.POST['new_password'])
					self.djangouser.save()
					self.appuser.needs_password_reset = False
					self.appuser.save()
					messages.success(request, 'Password updated, please log in again')
					logout(request)
					return redirect(reverse('login'))
				else:
					messages.error(request, 'New password fields must match')
			else:
				messages.error(request, 'Current password given is not correct')
		self.context['form'] = form
		return HttpResponse(self.template.render(self.context, request))



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
			self.appuser.save()

			messages.success(request, 'Updated user profile information')
			return redirect(reverse('profile'))
		else:
			self.context['form'] = form
			return HttpResponse(self.template.render(self.context, request))


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

		if not self.participant_details:
			return Http404('User not a participant on this exchange')

		if self.giftexchange:
			self.is_admin = self.appuser in self.giftexchange.admin_appuser.all()


class Dashboard(AuthenticatedView):
	""" Home page
		Lists all current gift exchanges that a user is participating in
		Has link to create a new gift exchange
	"""
	def get(self, request, *args, **kwargs):
		template = loader.get_template('giftexchange/dashboard.html')
		today = date.today()
		current_participation = Participant.objects.filter(appuser=self.appuser)
		current_exchanges = []
		past_exchanges = []
		for cp in current_participation:
			if cp.giftexchange.date >= today:
				current_exchanges.append(cp.giftexchange)
			else:
				past_exchanges.append(cp.giftexchange)

		context = {
			'breadcrumbs': [],
			'current_exchanges': current_exchanges,
			'appuser': self.appuser,
			'past_exchanges': past_exchanges,
		}

		return HttpResponse(template.render(context, request))


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
			GiftExchange.create(
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


class GiftExchangeDetail(GiftExchangeView):
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


class GiftExchangeDetailEdit(GiftExchangeView):
	""" View to handle updating the participant details of a gift exchange
		e.g., likes, dislikes, etc
	"""
	def setup(self, request, *args, **kwargs):
		super(GiftExchangeDetailEdit, self).setup(request, *args, **kwargs)
		self.template = loader.get_template('giftexchange/generic_form.html')
		self.context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				(self.giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Edit My Details', None)
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
			)
			return redirect(reverse('giftexchange_detail', kwargs={'giftexchange_id': self.giftexchange_id}))
		else:
			form = ParticipantDetailsForm(instance=self.participant_details)
			self.context['form'] = form
			return HttpResponse(self.template.render(self.context, request))

	def get(self, request, *args, **kwargs):
		form = ParticipantDetailsForm(instance=self.participant_details)
		self.context['form'] = form
		return HttpResponse(self.template.render(self.context, request))


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
		if not self.participant_details:
			raise Http404('User not a participant on this exchange')
		if not self.appuser in self.giftexchange.admin_appuser.all():
			raise Http404('User not an admin on this exchange')


class GiftExchangeAdminDetail(GiftExchangeAdminView):
	""" Admin view of gift exchange details
	"""
	def get(self, request, *args, **kwargs):
		template = loader.get_template('giftexchange/dashboard_manage.html')
		context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				(self.giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Admin', None)
			],
			'giftexchange': self.giftexchange
		}
		return HttpResponse(template.render(context, request))


class GiftExchangeEdit(GiftExchangeAdminView):
	""" Update handler for gift exchange details
	"""
	def setup(self, request, *args, **kwargs):
		super(GiftExchangeEdit, self).setup(request, *args, **kwargs)
		self.return_url = reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': self.giftexchange_id})
		self.context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				(self.giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Admin', reverse('giftexchange_detail', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Edit', None)
			],
			'form': None,
		}
		self.template = loader.get_template('giftexchange/generic_form.html')

	def post(self, request, *args, **kwargs):
		form = GiftExchangeDetailsForm(request.POST)
		if form.is_valid():
			self.giftexchange.update(
				description=request.POST['description'],
				spending_limit=request.POST['spending_limit'],
				location=request.POST['location'],
				date=request.POST['date'],
			)
			messages.success(request, 'Gift exchange details updated')
			return redirect(self.return_url)
		else:
			self.context['form'] = form
			return HttpResponse(self.template.render(self.context, request))

	def get(self, request, *args, **kwargs):
		self.context['form'] = GiftExchangeDetailsForm(instance=self.giftexchange)
		return HttpResponse(self.template.render(self.context, request))


class ViewAssignments(GiftExchangeAdminView):
	""" List view of gift exchange assigments
	"""
	def get(self, request, *args, **kwargs):
		template = loader.get_template('giftexchange/manage_assignments.html')
		context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				(self.giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Admin', reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Manage Assignments', None)
			],
			'giftexchange': self.giftexchange,
			'assignments': self.giftexchange.ordered_assignments
		}
		return HttpResponse(template.render(context, request))


class SetAssigments(GiftExchangeAdminView):
	""" Handler for generating gift exchange assignments
	"""
	def get(self, request, *args, **kwargs):
		self.giftexchange.generate_assignemnts()
		return redirect(reverse('giftexchange_manage_assignments', kwargs={'giftexchange_id': self.giftexchange_id}))


class ToggleAssignmentLock(GiftExchangeAdminView):
	""" Handler to toggle the locked state of gift exchange assignments
	"""
	def get(self, request, *args, **kwargs):
		if self.giftexchange.assignments_locked:
			self.giftexchange.unlock()
		else:
			self.giftexchange.lock()
		return redirect(reverse('giftexchange_manage_assignments', kwargs={'giftexchange_id': self.giftexchange_id}))


class ParticipantsList(GiftExchangeAdminView):
	""" List view of all gift exchange participants
	""" 
	def get(self, request, *args, **kwargs):
		participants = self.giftexchange.participant_set.all()

		template = loader.get_template('giftexchange/manage_participants.html')
		context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				(self.giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Admin', reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Manage Participants', None)
			],
			'giftexchange': self.giftexchange,
			'participants': participants,
		}
		return HttpResponse(template.render(context, request))


class ParticipantAdminAction(GiftExchangeAdminView):
	""" Base view for gift exchange admin pages that target a specific participant
	"""
	def setup(self, request, *args, **kwargs):
		super(ParticipantAdminAction, self).setup(request, *args, **kwargs)
		self.target_participant = Participant.objects.get(pk=kwargs['participant_id'])
		self.return_url = reverse('giftexchange_manage_participants', kwargs={'giftexchange_id': self.giftexchange_id})


class SetParticipantAdmin(ParticipantAdminAction):
	""" Sets a participant of a gift exchange to an admin
	"""
	def post(self, request, *args, **kwargs):
		self.giftexchange.admin_appuser.add(self.target_participant.appuser)
		self.giftexchange.save()
		messages.success(request, 'Participant added as admin')
		return redirect(self.return_url)

	def get(self, request, *args, **kwargs):		
		confirm_message = 'Add {} {} as an amdin of "{}"?'.format(
			self.target_participant.appuser.djangouser.first_name,
			self.target_participant.appuser.djangouser.last_name,
			self.giftexchange.title
		)
		template = loader.get_template('giftexchange/confirm_action.html')

		context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				(self.giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Admin', reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Manage Participants', self.return_url),
				('Remove Participant', None)
			],
			'confirm_message': confirm_message,
			'return_url': self.return_url,
		}
		return HttpResponse(template.render(context, request))


class UnsetParticipantAdmin(ParticipantAdminAction):
	""" Removes a participant of a gift exchange as an admin
	"""
	def post(self, request, *args, **kwargs):
		self.giftexchange.admin_appuser.remove(self.target_participant.appuser)
		self.giftexchange.save()
		messages.success(request, 'Participant removed as admin')
		return redirect(self.return_url)

	def get(self, request, *args, **kwargs):		
		confirm_message = 'Remove {} {} as an admin of "{}"?'.format(
			self.target_participant.appuser.djangouser.first_name,
			self.target_participant.appuser.djangouser.last_name,
			self.giftexchange.title
		)
		template = loader.get_template('giftexchange/confirm_action.html')

		context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				(self.giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Admin', reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Manage Participants', self.return_url),
				('Remove Participant', None)
			],
			'confirm_message': confirm_message,
			'return_url': self.return_url,
		}
		return HttpResponse(template.render(context, request))


class ParticipantUpload(GiftExchangeAdminView):
	""" Handler for uploading a CSV file of participants to a gift exchange
	"""
	def post(self, request, *args, **kwargs):
		error = False
		filehandle = request.FILES['file']
		if filehandle.multiple_chunks():
			messages.error('File is too large. Please split it into smaller files for upload.')
			error = True
		else:
			expected_header = ['first_name', 'last_name', 'email']
			lines = [line.decode("utf-8") for line in filehandle.readlines()]
			parsed_participants = csv_lines_to_dict(expected_header, lines)
			appusers = save_parsed_participants_as_appusers(parsed_participants)
			participants, created = self.giftexchange.add_participants(appusers)
			messages.success(request, 'Added {} participants to Gift Exchange'.format(created))
			return redirect(reverse('giftexchange_manage_participants', kwargs={'giftexchange_id': self.giftexchange.pk}))
		# just redirect to the GET if it failed
		return redirect(reverse('giftexchange_upload_participants', kwargs={'giftexchange_id': self.giftexchange.pk}))

	def get(self, request, *args, **kwargs):
		form = FileUploadForm()
		template = loader.get_template('giftexchange/participant_upload.html')
		context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				(self.giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Admin', reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Manage Participants', reverse('giftexchange_manage_participants', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Upload Participants', None)
			],
			'form': form
		}
		return HttpResponse(template.render(context, request))


class RemoveParticipant(ParticipantAdminAction):
	""" Handler for deleting a participant from a gift exchange
	"""
	def post(self, request, *args, **kwargs):
		self.target_participant.delete()
		messages.success(request, 'Participant removed from gift exchange')
		return redirect(self.return_url)

	def get(self, request, *args, **kwargs):	
		template = loader.get_template('giftexchange/confirm_action.html')
		confirm_message = 'Remove {} {} from gift exchange "{}"?'.format(
			self.target_participant.appuser.djangouser.first_name,
			self.target_participant.appuser.djangouser.last_name,
			self.giftexchange.title
		)
		context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				(self.giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Admin', reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Manage Participants', self.return_url),
				('Remove Participant', None)
			],
			'confirm_message': confirm_message,
			'return_url': self.return_url,
		}
		return HttpResponse(template.render(context, request))

