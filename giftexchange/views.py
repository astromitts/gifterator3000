from datetime import date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.template import loader
from django.http import HttpResponse, Http404
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.models import User

from giftexchange.forms import ParticipantDetailsForm, GiftExchangeDetailsForm, LoginForm
from giftexchange.models import Participant, AppUser, GiftExchange


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
		'current_exchanges': current_exchanges,
		'past_exchanges': past_exchanges,
	}

	return HttpResponse(template.render(context, request))


@login_required(login_url='/admin/')
def giftexchange_detail(request, giftexchange_id):
	appuser = AppUser.get(djangouser=request.user)
	giftexchange, particpant_details = _get_participant_and_exchange(appuser, giftexchange_id)
	assignment_details = None
	if giftexchange.assignments_locked:
		assignment_details = giftexchange.get_assignment(appuser)

	if not giftexchange:
		return Http404('Exchange not found')
	if not particpant_details:
		return Http404('User not a participant on this exchange')
	
	template = loader.get_template('giftexchange/giftexchange_detail.html')
	context = {
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
		'giftexchange': giftexchange,
		'assignments': giftexchange.ordered_assignments
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


