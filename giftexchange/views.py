from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.template import loader
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.models import User

from giftexchange.forms import (
	ParticipantDetailsForm, 
	GiftExchangeDetailsForm, 
	LoginForm, 
	GiftExchangeCreateForm,
	FileUploadForm,
)
from giftexchange.models import Participant, AppUser, GiftExchange
from giftexchange.utils import csv_lines_to_dict, save_parsed_participants_as_appusers

import csv


def login_handler(request):
	if request.user.is_authenticated:
		messages.info(request, 'You are already logged in')
		return redirect(reverse('dashboard'))

	template = loader.get_template('giftexchange/generic_form.html')
	if request.user.is_authenticated:
		return redirect(reverse('dashboard'))
	if request.POST:
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
					return HttpResponse(template.render(context, request))
			except Exception as exc:
				context = {
					'form': form
				}
				messages.error(request, 'Invalid email.')
				return HttpResponse(template.render(context, request))

	else:
		form = LoginForm()
		context = {
			'form': form
		}
	return HttpResponse(template.render(context, request))


def logout_handler(request):
    logout(request)
    return redirect(reverse('login'))


def _get_participant_and_exchange(appuser, giftexchange_id):
	giftexchange = None
	particpant_details = None

	giftexchange = GiftExchange.objects.filter(pk=giftexchange_id).first()
	
	if giftexchange:
		particpant_details = appuser.exchange_participant(giftexchange)
	return giftexchange, particpant_details


@login_required(login_url='/admin/')
def dashboard(request):
	template = loader.get_template('giftexchange/dashboard.html')
	today = date.today()
	appuser = AppUser.get(djangouser=request.user)
	current_participation = Participant.objects.filter(appuser=appuser)
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
		'appuser': appuser,
		'past_exchanges': past_exchanges,
	}

	return HttpResponse(template.render(context, request))


@login_required(login_url='/admin/')
def giftexchange_detail(request, giftexchange_id, appuser_id=None):
	admin_user = None
	if not appuser_id:
		appuser = AppUser.get(djangouser=request.user)
		giftexchange, particpant_details = _get_participant_and_exchange(appuser, giftexchange_id)
		breadcrumbs = [
			('dashboard', reverse('dashboard')),
			(giftexchange.title, None)
		]
	else:
		admin_user = AppUser.get(djangouser=request.user)
		if not admin_user.is_giftexchange_admin(giftexchange_id):
			return Http404('User not an admin on this exchange')
		appuser = AppUser.objects.get(pk=appuser_id)
		giftexchange, particpant_details = _get_participant_and_exchange(appuser, giftexchange_id)
		breadcrumbs = [
			('dashboard', reverse('dashboard')),
			(giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': giftexchange_id})),
			('Admin', reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': giftexchange_id})),
			('Manage Assignments', reverse('giftexchange_manage_assignments', kwargs={'giftexchange_id': giftexchange_id})),
			('{} {}'.format(appuser.djangouser.first_name, appuser.djangouser.last_name), None)
		]

	assignment_details = None
	if giftexchange.assignments_locked:
		assignment_details = giftexchange.get_assignment(appuser)

	if not giftexchange:
		return Http404('Exchange not found')
	if not particpant_details:
		return Http404('User not a participant on this exchange')
	
	template = loader.get_template('giftexchange/giftexchange_detail.html')
	context = {
		'breadcrumbs': breadcrumbs,
		'admin_user': admin_user,
		'appuser': appuser,
		'particpant_details': particpant_details,
		'assignment_details': assignment_details,
		'giftexchange': giftexchange
	}
	return HttpResponse(template.render(context, request))


@login_required(login_url='/admin/')
def giftexchange_detail_edit(request, giftexchange_id):
	appuser = AppUser.get(djangouser=request.user)
	giftexchange, particpant_details = _get_participant_and_exchange(appuser, giftexchange_id)
	
	if not giftexchange:
		return Http404('Exchange not found')
	if not particpant_details:
		return Http404('User not a participant on this exchange')

	template = loader.get_template('giftexchange/generic_form.html')

	if request.POST:
		form = ParticipantDetailsForm(request.POST)
		if form.is_valid():
			particpant_details.update(
				likes=request.POST['likes'],
				dislikes=request.POST['dislikes'],
				allergies_sensitivities=request.POST['allergies_sensitivities'],
			)
			return redirect(reverse('giftexchange_detail', kwargs={'giftexchange_id': giftexchange_id}))
	else:
		form = ParticipantDetailsForm(instance=particpant_details)

	context = {
		'breadcrumbs': [
			('dashboard', reverse('dashboard')),
			(giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': giftexchange_id})),
			('Edit My Details', None)
		],
		'form': form,
	}
	return HttpResponse(template.render(context, request))


@login_required(login_url='/admin/')
def giftexchange_manage_dashboard(request, giftexchange_id):
	appuser = AppUser.get(djangouser=request.user)
	giftexchange, particpant_details = _get_participant_and_exchange(appuser, giftexchange_id)
	if not giftexchange:
		return Http404('Exchange not found')
	if not particpant_details:
		return Http404('User not a participant on this exchange')
	if not appuser in giftexchange.admin_appuser.all():
		return Http404('User not an admin on this exchange')

	template = loader.get_template('giftexchange/dashboard_manage.html')
	context = {
		'breadcrumbs': [
			('dashboard', reverse('dashboard')),
			(giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': giftexchange_id})),
			('Admin', None)
		],
		'giftexchange': giftexchange
	}
	return HttpResponse(template.render(context, request))


@login_required(login_url='/admin/')
def giftexchange_manage_edit_details(request, giftexchange_id):
	appuser = AppUser.get(djangouser=request.user)
	giftexchange, particpant_details = _get_participant_and_exchange(appuser, giftexchange_id)
	
	if not giftexchange:
		return Http404('Exchange not found')
	if not particpant_details:
		return Http404('User not a participant on this exchange')
	if not appuser in giftexchange.admin_appuser.all():
		return Http404('User not an admin on this exchange')

	template = loader.get_template('giftexchange/generic_form.html')

	if request.POST:
		form = GiftExchangeDetailsForm(request.POST)
		if form.is_valid():
			giftexchange.update(
				description=request.POST['description'],
				spending_limit=request.POST['spending_limit'],
				location=request.POST['location'],
				date=request.POST['date'],
			)
			return redirect(reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': giftexchange_id}))
	else:
		form = GiftExchangeDetailsForm(instance=giftexchange)

	context = {
		'breadcrumbs': [
			('dashboard', reverse('dashboard')),
			(giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': giftexchange_id})),
			('Admin', reverse('giftexchange_detail', kwargs={'giftexchange_id': giftexchange_id})),
			('Edit', None)
		],
		'form': form,
	}
	return HttpResponse(template.render(context, request))


@login_required(login_url='/admin/')
def giftexchange_create_new(request):
	appuser = AppUser.get(djangouser=request.user)

	template = loader.get_template('giftexchange/generic_form.html')

	if request.POST:
		form = GiftExchangeCreateForm(request.POST)
		if form.is_valid():
			giftexchange = GiftExchange.create(
				title=request.POST['title'],
				description=request.POST['description'],
				spending_limit=request.POST['spending_limit'],
				location=request.POST['location'],
				date=request.POST['date'],
				appuser=appuser
			)
			return redirect(reverse('dashboard'))
	else:
		form = GiftExchangeCreateForm()

	context = {
		'breadcrumbs': [
			('dashboard', reverse('dashboard')),
			('Create A Gift Exchange', None)
		],
		'form': form,
	}
	return HttpResponse(template.render(context, request))


@login_required(login_url='/admin/')
def giftexchange_manage_assignments(request, giftexchange_id):
	appuser = AppUser.get(djangouser=request.user)
	giftexchange, particpant_details = _get_participant_and_exchange(appuser, giftexchange_id)
	
	if not giftexchange:
		return Http404('Exchange not found')
	if not particpant_details:
		return Http404('User not a participant on this exchange')
	if not appuser in giftexchange.admin_appuser.all():
		return Http404('User not an admin on this exchange')

	template = loader.get_template('giftexchange/manage_assignments.html')
	context = {
		'breadcrumbs': [
			('dashboard', reverse('dashboard')),
			(giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': giftexchange_id})),
			('Admin', reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': giftexchange_id})),
			('Manage Assignments', None)
		],
		'giftexchange': giftexchange,
		'assignments': giftexchange.ordered_assignments
	}
	return HttpResponse(template.render(context, request))


@login_required(login_url='/admin/')
def giftexchange_manage_participants(request, giftexchange_id):
	appuser = AppUser.get(djangouser=request.user)
	giftexchange, particpant_details = _get_participant_and_exchange(appuser, giftexchange_id)
	
	if not giftexchange:
		return Http404('Exchange not found')
	if not particpant_details:
		return Http404('User not a participant on this exchange')
	if not appuser in giftexchange.admin_appuser.all():
		return Http404('User not an admin on this exchange')

	participants = giftexchange.participant_set.all()

	template = loader.get_template('giftexchange/manage_participants.html')
	context = {
		'breadcrumbs': [
			('dashboard', reverse('dashboard')),
			(giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': giftexchange_id})),
			('Admin', reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': giftexchange_id})),
			('Manage Participants', None)
		],
		'giftexchange': giftexchange,
		'participants': participants,
	}
	return HttpResponse(template.render(context, request))


@login_required(login_url='/admin/')
def giftexchange_upload_participants(request, giftexchange_id):
	appuser = AppUser.get(djangouser=request.user)
	giftexchange, particpant_details = _get_participant_and_exchange(appuser, giftexchange_id)
	
	if not giftexchange:
		return Http404('Exchange not found')
	if not particpant_details:
		return Http404('User not a participant on this exchange')
	if not appuser in giftexchange.admin_appuser.all():
		return Http404('User not an admin on this exchange')

	template = loader.get_template('giftexchange/participant_upload.html')
	if request.POST:
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
			participants, created = giftexchange.add_participants(appusers)
			messages.success(request, 'Added {} participants to Gift Exchange'.format(created))
			return redirect(reverse('giftexchange_manage_participants', kwargs={'giftexchange_id': giftexchange.pk}))
	else:
		form = FileUploadForm()
	context = {
		'breadcrumbs': [
			('dashboard', reverse('dashboard')),
			(giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': giftexchange_id})),
			('Admin', reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': giftexchange_id})),
			('Manage Participants', reverse('giftexchange_manage_participants', kwargs={'giftexchange_id': giftexchange_id})),
			('Upload Participants', None)
		],
		'form': form
	}
	return HttpResponse(template.render(context, request))



@login_required(login_url='/admin/')
def giftexchange_remove_participant(request, giftexchange_id, participant_id):
	appuser = AppUser.get(djangouser=request.user)
	giftexchange, particpant_details = _get_participant_and_exchange(appuser, giftexchange_id)
	
	if not giftexchange:
		return Http404('Exchange not found')
	if not particpant_details:
		return Http404('User not a participant on this exchange')
	if not appuser in giftexchange.admin_appuser.all():
		return Http404('User not an admin on this exchange')

	target_participant = Participant.objects.get(pk=participant_id)
	return_url = reverse('giftexchange_manage_participants', kwargs={'giftexchange_id': giftexchange_id})

	confirm_message = 'Are you sure you want to remove {} {} as a participant of "{}"?'.format(
		target_participant.appuser.djangouser.first_name,
		target_participant.appuser.djangouser.last_name,
		giftexchange.title
	)
	template = loader.get_template('giftexchange/confirm_action.html')
	if request.POST:
		target_participant.delete()
		messages.success(request, 'Participant removed')
		return redirect(return_url)
	else:
		context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				(giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': giftexchange_id})),
				('Admin', reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': giftexchange_id})),
				('Manage Participants', return_url),
				('Remove Participant', None)
			],
			'confirm_message': confirm_message,
			'return_url': return_url,
		}
	return HttpResponse(template.render(context, request))


@login_required(login_url='/admin/')
def giftexchange_add_participant_admin(request, giftexchange_id, participant_id):
	appuser = AppUser.get(djangouser=request.user)
	giftexchange, particpant_details = _get_participant_and_exchange(appuser, giftexchange_id)
	
	if not giftexchange:
		return Http404('Exchange not found')
	if not particpant_details:
		return Http404('User not a participant on this exchange')
	if not appuser in giftexchange.admin_appuser.all():
		return Http404('User not an admin on this exchange')

	target_participant = Participant.objects.get(pk=participant_id)
	return_url = reverse('giftexchange_manage_participants', kwargs={'giftexchange_id': giftexchange_id})

	confirm_message = 'Add {} {} as an amdin of "{}"?'.format(
		target_participant.appuser.djangouser.first_name,
		target_participant.appuser.djangouser.last_name,
		giftexchange.title
	)
	template = loader.get_template('giftexchange/confirm_action.html')
	if request.POST:
		giftexchange.admin_appuser.add(target_participant.appuser)
		giftexchange.save()
		messages.success(request, 'Participant added as admin')
		return redirect(return_url)
	else:
		context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				(giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': giftexchange_id})),
				('Admin', reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': giftexchange_id})),
				('Manage Participants', return_url),
				('Remove Participant', None)
			],
			'confirm_message': confirm_message,
			'return_url': return_url,
		}
	return HttpResponse(template.render(context, request))

@login_required(login_url='/admin/')
def giftexchange_remove_participant_admin(request, giftexchange_id, participant_id):
	appuser = AppUser.get(djangouser=request.user)
	giftexchange, particpant_details = _get_participant_and_exchange(appuser, giftexchange_id)
	
	if not giftexchange:
		return Http404('Exchange not found')
	if not particpant_details:
		return Http404('User not a participant on this exchange')
	if not appuser in giftexchange.admin_appuser.all():
		return Http404('User not an admin on this exchange')

	target_participant = Participant.objects.get(pk=participant_id)
	return_url = reverse('giftexchange_manage_participants', kwargs={'giftexchange_id': giftexchange_id})

	confirm_message = 'Remove {} {} as an amdin of "{}"?'.format(
		target_participant.appuser.djangouser.first_name,
		target_participant.appuser.djangouser.last_name,
		giftexchange.title
	)
	template = loader.get_template('giftexchange/confirm_action.html')
	if request.POST:
		giftexchange.admin_appuser.remove(target_participant.appuser)
		giftexchange.save()
		messages.success(request, 'Participant removed as admin')
		return redirect(return_url)
	else:
		context = {
			'breadcrumbs': [
				('dashboard', reverse('dashboard')),
				(giftexchange.title, reverse('giftexchange_detail', kwargs={'giftexchange_id': giftexchange_id})),
				('Admin', reverse('giftexchange_manage_dashboard', kwargs={'giftexchange_id': giftexchange_id})),
				('Manage Participants', return_url),
				('Remove Participant', None)
			],
			'confirm_message': confirm_message,
			'return_url': return_url,
		}
	return HttpResponse(template.render(context, request))


@login_required(login_url='/admin/')
def giftexchange_set_assignments(request, giftexchange_id):
	appuser = AppUser.get(djangouser=request.user)
	giftexchange, particpant_details = _get_participant_and_exchange(appuser, giftexchange_id)
	
	if not giftexchange:
		return Http404('Exchange not found')
	if not particpant_details:
		return Http404('User not a participant on this exchange')
	if not appuser in giftexchange.admin_appuser.all():
		return Http404('User not an admin on this exchange')

	giftexchange.generate_assignemnts()
	return redirect(reverse('giftexchange_manage_assignments', kwargs={'giftexchange_id': giftexchange_id}))


@login_required(login_url='/admin/')
def giftexchange_toggle_assignment_lock(request, giftexchange_id):
	appuser = AppUser.get(djangouser=request.user)
	giftexchange, particpant_details = _get_participant_and_exchange(appuser, giftexchange_id)
	
	if not giftexchange:
		return Http404('Exchange not found')
	if not particpant_details:
		return Http404('User not a participant on this exchange')
	if not appuser in giftexchange.admin_appuser.all():
		return Http404('User not an admin on this exchange')
	if giftexchange.assignments_locked:
		giftexchange.unlock()
	else:
		giftexchange.lock()
	return redirect(reverse('giftexchange_manage_assignments', kwargs={'giftexchange_id': giftexchange_id}))


