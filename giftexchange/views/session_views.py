from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import loader
from django.urls import reverse
from django.views import View

from giftexchange.views.base_views import AuthenticatedView, UnAuthenticatedView
from giftexchange.forms import LoginForm, RegisterForm
from giftexchange.models import AppUser, AppInvitation, MagicLink

from datetime import datetime


class RegistrationHandler(UnAuthenticatedView):
	""" View for registering for the App
	"""
	def setup(self, request, *args, **kwargs):
		super(RegistrationHandler, self).setup(request, *args, **kwargs)
		self.template = loader.get_template('giftexchange/generic_form.html')
		self.context = {'mediumwidth': True}

	def get(self, request, *args, **kwargs):
		super(RegistrationHandler, self).get(request, *args, **kwargs)
		self.context['form'] = RegisterForm()
		return HttpResponse(self.template.render(self.context, request))

	def post(self, request, *args, **kwargs):
		data = request.POST.copy()
		form = RegisterForm(data)
		self.context['form'] = form

		if form.is_valid():
			user_exists = User.objects.filter(email=data['email']).exists()
			if user_exists:
				messages.error(request, 'A user with this email address already exists')
				return HttpResponse(self.template.render(self.context, request))
			else:
				djangouser = User(
					email=data['email'],
					username=data['email'],
					first_name=data['first_name'],
					last_name=data['last_name']
				)
				djangouser.save()
				appuser = AppUser.objects.create(djangouser=djangouser)
				has_invitations = AppInvitation.objects.filter(invitee_email=djangouser.email)
				if has_invitations:
					for invitation in has_invitations:
						invitation.giftexchange.add_participant(appuser)
						invitation.status = 'accepted'
						invitation.save()
				messages.success(request, 'You registered to Gifterator 3000! Please confirm your email address and login to continue!')
				return redirect(reverse('login'))
		else:
			context = {
				'form': form
			}
			return HttpResponse(self.template.render(context, request))



class LoginHandler(UnAuthenticatedView):
	""" View for Log in:
			GET: Provides form for a magic link to be sent to given email address
			POST: verifies email address is for a registered user, generates link
				  and sends off the email
	"""
	def setup(self, request, *args, **kwargs):
		super(LoginHandler, self).setup(request, *args, **kwargs)
		self.template = loader.get_template('giftexchange/generic_form.html')
		self.context = {}

	def get(self, request, *args, **kwargs):
		super(LoginHandler, self).get(request, *args, **kwargs)
		if request.user.is_authenticated:
			messages.info(request, 'You are already logged in')
			return redirect(reverse('dashboard'))
		elif request.GET.get('token') and request.GET.get('email'):
			magic_link_qs = MagicLink.objects.filter(
				token=request.GET['token'],
				expiration__gte=datetime.now(),
				user_email=request.GET.get('email')
			)
			if magic_link_qs.exists():
				magic_link = magic_link_qs.first()
				user = User.objects.get(email=request.GET['email'])
				login(request, user)
				messages.success(request, 'Welcome! You are logged in!')
				magic_link.delete()
				return redirect(reverse('dashboard'))
			else:
				messages.error(request, 'Could not validate your login token. Please request a new one.')

		self.context['form'] = LoginForm()
		self.context['submit_text'] = 'Email me a login link'
		return HttpResponse(self.template.render(self.context, request))

	def post(self, request, *args, **kwargs):
		self.template = loader.get_template('giftexchange/generic_form.html')
		data = request.POST.copy()
		form = LoginForm(data)
		if form.is_valid():
			try:
				user = User.objects.get(email=data['email'])
			except User.DoesNotExist as exc:
				context = {
					'form': form
				}
				messages.error(request, 'Invalid email.')
				return HttpResponse(self.template.render(context, request))

			magic_link = MagicLink(user_email=data['email'])
			magic_link.save()
			magic_link.send_link_email(request)
			self.context['form'] = form
			self.context['submit_text'] = 'Email me a login link'
			messages.success(request, 'Link sent. Check your email.')
			return HttpResponse(self.template.render(self.context, request))
		else:
			self.context['form'] = form
			return HttpResponse(self.template.render(self.context, request))


def logout_handler(request):
	""" View for log out
	"""
	logout(request)
	return redirect(reverse('login'))
