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
	RegisterForm,
	FileUploadForm,
)
from giftexchange.models import (
	AppInvitation,
	AppUser,
	Participant,
	ExchangeAssignment,
	MagicLink,
	AdminInvitation,
	oneweekfromnow
)
from giftexchange.utils import csv_lines_to_dict


class GiftExchangeAdminDetail(GiftExchangeAdminView):
	""" Admin view of gift exchange details
	"""
	def get(self, request, *args, **kwargs):
		template = loader.get_template('giftexchange/dashboard_manage.html')
		context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				(self.giftexchange.title, None)
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
				ship_gifts_allowed=request.POST.get('ship_gifts_allowed', 'off') == 'on',
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
				(self.giftexchange.title, reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': self.giftexchange_id})),
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
				(self.giftexchange.title, reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Manage Participants', None)
			],
			'giftexchange': self.giftexchange,
			'participants': participants,
		}
		return HttpResponse(template.render(context, request))

class AddSingleUser(GiftExchangeAdminView):
	""" Handler for inviting a new user to the App
	"""
	def setup(self, request, *args, **kwargs):
		super(AddSingleUser, self).setup(request, *args, **kwargs)
		self.template = loader.get_template('giftexchange/generic_form.html')
		self.return_url = reverse('giftexchange_manage_participants', kwargs={'giftexchange_id': self.giftexchange_id})
		self.context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				(self.giftexchange.title, reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Manage Participants', self.return_url),
				('Add a New Participant', None)
			],
			'mediumwidth': True,
		}

	def get(self, request, *args, **kwargs):
		self.context['form'] = RegisterForm()
		return HttpResponse(self.template.render(self.context, request))

	def post(self, request, *args, **kwargs):
		form = RegisterForm(request.POST)
		if form.is_valid():
			participant_data = request.POST
			particpant, participant_created = Participant.patch(
				email=participant_data['email'],
				first_name=participant_data['first_name'],
				last_name=participant_data['last_name'],
				giftexchange=self.giftexchange,
				status='active'
			)
			if participant_created:
				messages.success(request, 'Added {} {} to Gift Exchange'.format(participant_data['first_name'], participant_data['last_name']))
				return redirect(reverse('giftexchange_manage_participants', kwargs={'giftexchange_id': self.giftexchange.pk}))
			else:
				messages.error(request, error_message)
				return redirect(reverse('giftexchange_invite_new_user', kwargs={'giftexchange_id': self.giftexchange.id}))


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
				(self.giftexchange.title, reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': self.giftexchange_id})),
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
				particpant, participant_created = Participant.patch(
					email=participant_data['email'],
					first_name=participant_data['first_name'],
					last_name=participant_data['last_name'],
					likes=participant_data['likes'],
					dislikes=participant_data['dislikes'],
					allergies_sensitivities=participant_data['allergies'],
					shipping_address=participant_data['shipping_address'],
					giftexchange=self.giftexchange,
					status='active'
				)
				if participant_created:
					added_count += 1
			messages.success(request, 'Added {} participants to Gift Exchange'.format(added_count))
			return redirect(reverse('giftexchange_manage_participants', kwargs={'giftexchange_id': self.giftexchange.pk}))
		# just redirect to the GET if it failed
		return redirect(reverse('giftexchange_upload_participants', kwargs={'giftexchange_id': self.giftexchange.pk}))

	def get(self, request, *args, **kwargs):
		form = FileUploadForm()
		template = loader.get_template('giftexchange/participant_upload.html')
		context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				(self.giftexchange.title, reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': self.giftexchange_id})),
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
			self.target_participant.first_name,
			self.target_participant.last_name,
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


class PreviewAssignmentEmail(GiftExchangeAdminView):
	def _render_email_for_participant(self, target_participant):

		assignment = ExchangeAssignment.objects.get(
			giver=target_participant,
			giftexchange=self.giftexchange
		)
		return assignment.render_assignment_email()

	def get(self, request, *args, **kwargs):
		template = loader.get_template('giftexchange/emails_preview.html')
		return_url = reverse('giftexchange_manage_assignments', kwargs={'giftexchange_id': self.giftexchange_id})
		if kwargs.get('target_participant_id'):
			participant = Participant.objects.get(pk=kwargs['target_participant_id'])
			assignment = ExchangeAssignment.objects.get(giver=participant)
			send_all = False
		else:
			send_all = True

		context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				(self.giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Admin', reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Manage Assignments', return_url),
				('Preview Assignment Email', None)
			],
			'return_url': return_url,
			'emails': []
		}

		if send_all:
			target_participants = Participant.objects.filter(giftexchange=self.giftexchange, status='active').all()
		else:
			target_participants = [assignment.giver, ]
		for participant in target_participants:
			context['emails'].append(self._render_email_for_participant(participant))

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
		if kwargs.get('target_participant_id'):
			self.participant = Participant.objects.get(pk=kwargs['target_participant_id'])
			self.assignment = ExchangeAssignment.objects.get(giver=self.participant)
			confirm_message = 'Send assignment email to {}?'.format(self.participant.name)
			self.send_all = False
		else:
			self.send_all = True
			confirm_message = 'Send assignment emails to ALL participants?'

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
			target_participants = [self.assignment.giver, ]
			success_message = 'Assignment email sent to {}'.format(self.assignment.giver.name)
		for participant in target_participants:
			self._send_email_for_participant(participant)

		messages.success(
			request,
			success_message
		)
		return redirect(self.return_url)


class InviteAdmin(GiftExchangeAdminView):
	def setup(self, request, *args, **kwargs):
		super(InviteAdmin, self).setup(request, *args, **kwargs)
		self.participant = Participant.objects.get(pk=kwargs['participant_id'])
		self.template = loader.get_template('giftexchange/confirm_action.html')
		self.return_url = reverse('giftexchange_manage_participants', kwargs={'giftexchange_id': self.giftexchange.pk})
		if self.participant.appuser:
			confirm_message = 'Set {} as an admin on this gift exchange?'.format(self.participant.name)
			self.needs_invite = False
		else:
			confirm_message = '{} does not have an account on Gifterator3k. Send them an invitation? (Once they accept, they will be added as an admin to this gift exchange)'.format(self.participant.name)
			self.needs_invite = True
		self.context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				(self.giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Admin', reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': self.giftexchange_id})),
				('Manage Participants', self.return_url),
				('Add Admin', None)
			],
			'confirm_message': confirm_message,
			'return_url': self.return_url,
		}

	def get(self, request, *args, **kwargs):
		return HttpResponse(self.template.render(self.context, request))

	def post(self, request, *args, **kwargs):
		if self.needs_invite:
			magic_link = MagicLink(user_email=self.participant.email, expiration=oneweekfromnow())
			magic_link.save()
			admin_invitation = AdminInvitation(
				inviter=self.appuser,
				participant=self.participant,
				giftexchange=self.giftexchange,
				status='pending',
				magic_link=magic_link
			)
			admin_invitation.save()
			admin_invitation.send_invitation(request)
			success_message = 'Sent an registration invitation to {}'.format(self.participant.name)
		else:
			self.giftexchange.admin_appuser.add(self.participant.appuser)
			self.giftexchange.save()
			success_message = 'Set {} as an admin'.format(self.participant.name)

		messages.success(
			request,
			success_message
		)
		return redirect(self.return_url)
