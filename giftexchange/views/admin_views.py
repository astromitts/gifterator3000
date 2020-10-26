from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import loader
from django.urls import reverse
from django.core.files.storage import FileSystemStorage

from giftexchange.views.base_views import GiftExchangeAdminView, ParticipantAdminAction
from giftexchange.forms import (
	GiftExchangeDetailsForm,
	ParticipantSearchForm,
	EmailForm,
	FileUploadForm,
)
from giftexchange.models import AppInvitation, AppUser, Participant, ExchangeAssignment, MagicLink
from giftexchange.utils import csv_lines_to_dict


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
		pending_invitations = AppInvitation.objects.filter(giftexchange=self.giftexchange)

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
			'pending_invitations': pending_invitations,
		}
		return HttpResponse(template.render(context, request))


class ParticipantsSearch(GiftExchangeAdminView):
	""" List view of all gift exchange participants
	"""
	def get(self, request, *args, **kwargs):
		template = loader.get_template('giftexchange/participants_add_search.html')
		accepted_search_fields = ['email', 'first_name', 'last_name']
		context = {'mediumwidth': True}
		result_users = []
		if any(field in request.GET.keys() for field in accepted_search_fields):
			form = ParticipantSearchForm(request.GET)
			qs = User.objects
			if request.GET.get('email'):
				qs = qs.filter(email__contains=request.GET['email'])
			if request.GET.get('first_name'):
				qs = qs.filter(first_name__contains=request.GET['first_name'])
			if request.GET.get('email'):
				qs = qs.filter(last_name__contains=request.GET['last_name'])
			result_users = qs.all()
		else:
			form = ParticipantSearchForm()
		context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				(self.giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Admin', reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Manage Participants', reverse('giftexchange_manage_participants', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Search Participants', None)
			],
			'form': form,
			'mediumwidth': True,
			'method': 'GET',
			'result_users': result_users,
			'giftexchange': self.giftexchange,
		}
		result_participants = []
		return HttpResponse(template.render(context, request))


class ParticipantsAddFromSearch(GiftExchangeAdminView):
	""" Handler for adding a selected list off users to a given Gift Exchange
	"""
	def post(self, request, *args, **kwargs):
		invited_appusers = []
		created_count = 0
		for field in request.POST.keys():
			if field.startswith('invite_user_'):
				appuser = AppUser.objects.get(pk=int(request.POST.get(field)))
				invited_appusers.append(appuser)
				participant, created = self.giftexchange.add_participant(appuser)
				if created:
					created_count += 1
		if created_count > 0:
			messages.success(request, 'Invited {} participants'.format(created_count))
		else:
			messages.error(request, 'No new invitations to make')
		return redirect(reverse('giftexchange_manage_participants', kwargs={'giftexchange_id': self.giftexchange.id}))


class InviteNewUser(GiftExchangeAdminView):
	""" Handler for inviting a new user to the App
	"""
	def setup(self, request, *args, **kwargs):
		super(InviteNewUser, self).setup(request, *args, **kwargs)
		self.template = loader.get_template('giftexchange/generic_form.html')
		self.return_url = reverse('giftexchange_manage_participants', kwargs={'giftexchange_id': self.giftexchange_id})
		self.context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				(self.giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Admin', reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Manage Participants', self.return_url),
				('Invite a New User', None)
			],
			'mediumwidth': True,
		}

	def get(self, request, *args, **kwargs):
		self.context['form'] = EmailForm()
		return HttpResponse(self.template.render(self.context, request))

	def post(self, request, *args, **kwargs):
		form = EmailForm(request.POST)
		if form.is_valid():
			invitation, created, reason = AppInvitation.get_or_create(
				inviter=self.appuser,
				invitee_email=request.POST['email'],
				giftexchange=self.giftexchange
			)
			if created:
				registration_url = self._full_url_reverse(request, 'register')
				invitation.send_invitation_for_new_user(registration_url)
				messages.success(request, 'Invitation sent to {}'.format(request.POST['email']))
				return redirect(self.return_url)
			else:
				messages.error(request, reason)
				return redirect(reverse('giftexchange_invite_new_user', kwargs={'giftexchange_id': self.giftexchange.id}))


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
		added_count = 0
		invited_count = 0
		if filehandle.multiple_chunks():
			messages.error('File is too large. Please split it into smaller files for upload.')
			return redirect(reverse('giftexchange_upload_participants', kwargs={'giftexchange_id': self.giftexchange.pk}))
		else:
			expected_header = ['first_name', 'last_name', 'email', 'shipping_address', 'likes', 'dislikes', 'allergies']
			fs = FileSystemStorage()
			filename = fs.save('user-uploads/appuserupload-{}-{}'.format(self.appuser.pk, filehandle.name), filehandle)
			parsed_participants, error = csv_lines_to_dict(expected_header, filename)
			fs.delete(filename)
			if error:
				messages.error(request, error)
				return redirect(reverse('giftexchange_upload_participants', kwargs={'giftexchange_id': self.giftexchange.pk}))
			for participant_data in parsed_participants:
				djangouser_exists = User.objects.filter(email=participant_data['email']).exists()
				if not djangouser_exists:
					djangouser = User(
						email=participant_data['email'],
						username=participant_data['email'],
						first_name=participant_data['first_name'],
						last_name=participant_data['last_name']
					)
					djangouser.save()
				else:
					djangouser = User.objects.get(email=participant_data['email'])

				appuser_exists = AppUser.objects.filter(djangouser=djangouser).exists()
				if not appuser_exists:
					appuser = AppUser.create(
						djangouser=djangouser,
						likes=participant_data['likes'],
						dislikes=participant_data['dislikes'],
						allergies_sensitivities=participant_data['allergies'],
						shipping_address=participant_data['shipping_address']
					)
				else:
					appuser = AppUser.objects.get(djangouser=djangouser)

				participant, created = Participant.get_or_create(
					appuser,
					giftexchange=self.giftexchange,
					likes=participant_data['likes'],
					dislikes=participant_data['dislikes'],
					allergies_sensitivities=participant_data['allergies'],
					shipping_address=participant_data['shipping_address']
				)
				if created:
					added_count += 1

				# cleanup any existing invitations
				AppInvitation.objects.filter(
					inviter=self.appuser,
					invitee_email=participant_data['email'],
					giftexchange=self.giftexchange
				).delete()
				magic_link = MagicLink(user_email=participant_data['email'])
				magic_link.save()
				invitation = AppInvitation(inviter=self.appuser, invitee_email=participant_data['email'], giftexchange=self.giftexchange)
				invitation.save()
				invitation.send_invitation_for_new_user(magic_link.full_link(request))
				invited_count += 1

			messages.success(request, 'Added {} participants to Gift Exchange and invited {} users'.format(added_count, invited_count))
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
			'form': form,
			'giftexchange': self.giftexchange,
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


class SendAssignmentEmail(GiftExchangeAdminView):
	def _send_email_for_participant(self, target_participant):

		assignment = ExchangeAssignment.objects.get(
			giver=target_participant,
			giftexchange=self.giftexchange
		)
		assignment.send_assignment_email()

	def setup(self, request, *args, **kwargs):
		super(SendAssignmentEmail, self).setup(request, *args, **kwargs)
		self.template = loader.get_template('giftexchange/confirm_action.html')
		self.return_url = reverse('giftexchange_manage_assignments', kwargs={'giftexchange_id': self.giftexchange_id})
		if kwargs.get('target_appuser_id'):
			self.target_appuser = AppUser.objects.get(pk=kwargs['target_appuser_id'])
			confirm_message = 'Send assignment email to {} {}?'.format(
				assignment.giver.appuser.djangouser.first_name,
				assignment.giver.appuser.djangouser.last_name
			)
			self.send_all = False
		else:
			self.send_all = True
			confirm_message = 'Send assignment emails to all participants?'

		self.context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				(self.giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Admin', reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Manage Assignments', self.return_url),
				('Send Assignment Email', None)
			],
			'confirm_message': confirm_message,
			'return_url': self.return_url,
		}

	def get(self, request, *args, **kwargs):
		return HttpResponse(self.template.render(self.context, request))

	def post(self, request, *args, **kwargs):

		if self.send_all:
			target_participants = Participant.objects.filter(giftexchange=self.giftexchange, status='active').all()
			success_message = 'Assignment emails sent to active users.'
		else:
			target_participants = [Participant.objects.get(appuser=target_appuser, giftexchange=self.giftexchange), ]
			success_message = 'Assignment email sent to {} {}'.format(
				self.assignment.giver.appuser.djangouser.first_name,
				self.assignment.giver.appuser.djangouser.last_name
			)
		for participant in target_participants:
			self._send_email_for_participant(participant)

		messages.success(
			request,
			success_message
		)
		return redirect(self.return_url)

