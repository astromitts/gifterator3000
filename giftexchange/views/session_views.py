from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import loader
from django.urls import reverse
from django.views import View


from giftexchange.views.base_views import AuthenticatedView

from giftexchange.forms import (
	LoginForm,
	PasswordResetForm,
	PasswordChangeForm,
	RegisterForm,
)

from giftexchange.models import AppUser, AppInvitation


class RegistrationHandler(View):
	""" View for registering for the App
	"""
	def setup(self, request, *args, **kwargs):
		super(RegistrationHandler, self).setup(request, *args, **kwargs)
		self.template = loader.get_template('giftexchange/generic_form.html')
		self.context = {'mediumwidth': True}

	def get(self, request, *args, **kwargs):
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
				if data['password'] == data['confirm_password']:
					djangouser = User(
						email=data['email'],
						username=data['email'],
						first_name=data['first_name'],
						last_name=data['last_name']
					)
					djangouser.save()
					djangouser.set_password(data['password'])
					djangouser.save()
					appuser = AppUser.objects.create(djangouser=djangouser, needs_password_reset=False)
					has_invitations = AppInvitation.objects.filter(invitee_email=djangouser.email)
					if has_invitations:
						for invitation in has_invitations:
							invitation.giftexchange.add_participant(appuser)
							invitation.status = 'accepted'
							invitation.save()
					messages.success(request, 'You registered to Gifterator 3000! Please login to continue!')
					return redirect(reverse('dashboard'))
				else:
					messages.error(request, 'Password fields must match')
		else: 
			context = {
				'form': form
			}
			return HttpResponse(self.template.render(context, request))



class LoginHandler(View):
	""" View for Log in
	"""
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
			except User.DoesNotExist as exc:
				context = {
					'form': form
				}
				messages.error(request, 'Invalid email.')
				return HttpResponse(self.template.render(context, request))

			if user.check_password(data['password']):
				appuser = AppUser.get(djangouser=user)
				if appuser.needs_password_reset:
					messages.error(request, 'You must set a new password to proceed')
					return redirect(reverse('reset_password'))
				else:
					login(request, user)
					return redirect(reverse('dashboard'))
			else: 
				context = {
					'form': form
				}
				messages.error(request, 'Invalid password.')
				return HttpResponse(self.template.render(context, request))
		else:
			self.context['form'] = form
			return HttpResponse(self.template.render(self.context, request))


def logout_handler(request):
	""" View for log out
	"""
	logout(request)
	return redirect(reverse('login'))


class ResetPassword(View):
	""" View for resetting user password
	"""
	def setup(self, request, *args, **kwargs):
		super(ResetPassword, self).setup(request, *args, **kwargs)
		self.template = loader.get_template('giftexchange/generic_form.html')
		self.context = {}

	def get(self, request, *args, **kwargs):
		self.context['form'] = PasswordResetForm()
		return HttpResponse(self.template.render(self.context, request))

	def post(self, request, *args, **kwargs):
		data = request.POST.copy()
		form = PasswordResetForm(data)
		if form.is_valid():
			try:
				djangouser = User.objects.get(email=data['email'])
			except Exception as exc:
				self.context['form'] = form
				messages.error(request, 'Invalid email.')
				return HttpResponse(self.template.render(context, request))
			if djangouser.check_password(data['current_password']):
				if request.POST['new_password'] == request.POST['confirm_new_password']:
					djangouser.set_password(request.POST['new_password'])
					djangouser.save()
					appuser = AppUser.objects.get(djangouser=djangouser)
					appuser.needs_password_reset = False
					appuser.save()
					messages.success(request, 'Password updated, please log in again')
					return redirect(reverse('login'))
				else:
					messages.error(request, 'New password fields must match')
			else:
				messages.error(request, 'Current password given is not correct')
		self.context['form'] = form
		return HttpResponse(self.template.render(self.context, request))


class ChangePassword(AuthenticatedView):
	""" Handler for a logged in user to change their password
	"""
	def setup(self, request, *args, **kwargs):
		super(ChangePassword, self).setup(request, *args, **kwargs)
		self.template = loader.get_template('giftexchange/generic_form.html')
		self.context = {}

	def get(self, request, *args, **kwargs):
		self.context['form'] = PasswordChangeForm()
		return HttpResponse(self.template.render(self.context, request))

	def post(self, request, *args, **kwargs):
		data = request.POST.copy()
		form = PasswordChangeForm(data)
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
