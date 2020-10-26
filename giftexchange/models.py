from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string
from datetime import datetime, timedelta

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

import random
import string
import hashlib


def twentyfourhoursfromnow():
	return datetime.now() + timedelta(1)


def generate_login_token(email):
	token_base = '{}-{}-{}'.format(
		email,
		datetime.now(),
		''.join(random.choices(string.ascii_uppercase + string.digits, k = 60))
	)
	token_hash = hashlib.sha256(token_base.encode())
	return token_hash.hexdigest()

def send_email(subject, html_body, to_emails):
	message = Mail(
		from_email=settings.FROM_ADDRESS,
		to_emails=to_emails,
		subject=subject,
		html_content=html_body
	)
	sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
	response = sg.send(message)
	return response


class AppUser(models.Model):
	djangouser = models.OneToOneField(User, on_delete=models.CASCADE)
	default_likes = models.TextField(blank=True, null=True)
	default_dislikes = models.TextField(blank=True, null=True)
	default_allergies_sensitivities = models.TextField(blank=True, null=True)
	default_shipping_address = models.TextField(blank=True, null=True)

	def __str__(self):
		return '{} {} ({})'.format(self.djangouser.first_name, self.djangouser.last_name, self.djangouser.email)

	def is_giftexchange_admin(self, giftexchange_id):
		giftexchange = GiftExchange.objects.get(pk=giftexchange_id)
		return self in giftexchange.admin_appuser.all()

	def exchange_participant(self, giftexchange):
		participant_exists = Participant.objects.filter(appuser=self, giftexchange=giftexchange).exists()
		if participant_exists:
			return Participant.objects.get(appuser=self, giftexchange=giftexchange)
		return False

	@classmethod
	def create(cls, djangouser, likes=None, dislikes=None, allergies_sensitivities=None, shipping_address=None):
		appuser = cls(djangouser=djangouser)
		if likes:
			appuser.default_likes = likes
		if dislikes:
			appuser.default_dislikes = dislikes
		if allergies_sensitivities:
			appuser.default_allergies_sensitivities = allergies_sensitivities
		if shipping_address:
			appuser.default_shipping_address = shipping_address
		appuser.save()
		return appuser

	@classmethod
	def get_or_create_djangouser(cls, email, first_name, last_name):
		created = False
		djangouser_exists = User.objects.filter(email=email).exists()
		if djangouser_exists:
			created = False
			djangouser = User.objects.get(email=email)
		else:
			djangouser = User(
				email=email,
				username=email,
				first_name=first_name,
				last_name=last_name
			)
			djangouser.save()
			created = True
		return djangouser, created

	@classmethod
	def get_or_create(cls, djangouser):
		appuser_exists = cls.objects.filter(djangouser=djangouser).exists()
		if appuser_exists:
			created = False
			appuser = cls.objects.get(djangouser=djangouser)
		else:
			appuser = cls.create(djangouser)
			created = True
		return appuser, created

	@classmethod
	def get(cls, djangouser):
		return cls.objects.get(djangouser=djangouser)

	@classmethod
	def get_by_email(cls, email):
		djangouser_exists = User.objects.filter(email=email).exists()
		if djangouser_exists:
			return cls.objects.get(djangouser=djangouser)
		return None


class MagicLink(models.Model):
	expiration = models.DateTimeField(default=twentyfourhoursfromnow)
	user_email = models.EmailField()
	token = models.CharField(max_length=64)

	def tmp_password(self):
		return generate_login_token(self.user_email)

	def full_link(self, request):
		return '{}://{}{}?token={}&email={}'.format(
			request.scheme,
			request.get_host(),
			reverse('login'),
			self.token,
			self.user_email
		)

	def save(self, *args, **kwargs):
		if not self.pk:
			self.token = generate_login_token(self.user_email)
		super(MagicLink, self).save(*args, **kwargs)
		dupes = MagicLink.objects.filter(user_email=self.user_email).exclude(pk=self.pk).delete()

	def send_link_email(self, request):
		subject = 'Gifterator3000 login link'
		formatted_body = render_to_string(
			'giftexchange/emails/send_magic_link.html',
			context={
				'login_link': self.full_link(request),
			}
		)
		email_result = send_email(
			subject=subject,
			to_emails=self.user_email,
			html_body=formatted_body
		)

	def __str__(self):
		return '{} // expires: {}'.format(self.user_email, self.expiration)


class GiftExchange(models.Model):
	title = models.CharField(max_length=300, unique=True)
	date = models.DateField(blank=True, null=True)
	location = models.CharField(max_length=500)
	description = models.TextField(blank=True, null=True)
	spending_limit = models.IntegerField(default=0)
	admin_appuser = models.ManyToManyField(AppUser)
	assignments_locked = models.BooleanField(default=False)
	ship_gifts_allowed = models.BooleanField(default=False)

	def get_assignment(self, giver_appuser):
		giver_participant = Participant.objects.get(giftexchange=self, appuser=giver_appuser)
		return ExchangeAssignment.objects.filter(giftexchange=self, giver=giver_participant).first().reciever

	def get_giver(self, reciever_appuser):
		reciever_participant = Participant.objects.get(giftexchange=self, appuser=reciever_appuser)
		return ExchangeAssignment.objects.filter(giftexchange=self, reciever=reciever_participant).first().giver

	def get_participant(self, appuser):
		return Participant.objects.get(giftexchange=self, appuser=appuser)

	@property
	def has_assignments(self):
		return ExchangeAssignment.objects.filter(giftexchange=self).exists()

	def lock(self):
		self.assignments_locked = True
		self.save()

	def unlock(self):
		self.assignments_locked = False
		self.save()

	@property
	def ordered_assignments(self):
		assignments = []
		if self.exchangeassignment_set.count() > 0:
			start_assignment = self.exchangeassignment_set.order_by('pk').first()
			next_assignment = start_assignment
			next_giver = start_assignment.reciever
			while next_assignment.reciever != start_assignment.giver:
				assignments.append(next_assignment)
				next_assignment = self.exchangeassignment_set.all().get(giver=next_assignment.reciever)
				next_giver = next_assignment.reciever
			assignments.append(next_assignment)
		return assignments

	def update(self, date, location, description, spending_limit, ship_gifts_allowed):
		self.date = date
		self.location = location
		self.description = description
		self.spending_limit = spending_limit
		self.ship_gifts_allowed = ship_gifts_allowed
		self.save()

	@classmethod
	def create(cls, title, date, location, description, spending_limit, appuser):
		new_instance = cls(
			title=title,
			date=date,
			location=location,
			description=description,
			spending_limit=spending_limit
		)
		new_instance.save()
		new_instance.admin_appuser.add(appuser)
		participant = Participant(giftexchange=new_instance, appuser=appuser, status='active')
		participant.save()
		return new_instance

	@classmethod
	def get_or_create(cls, title):
		created = False
		giftexchange_exists = cls.objects.filter(title=title).exists()
		if giftexchange_exists:
			giftexchange = cls.objects.get(title=title)
			created = False
		else:
			giftexchange = cls(title=title)
			giftexchange.save()
			created = True
		return giftexchange, created

	def add_participant(self, appuser, delete_assignments=False):
		if delete_assignments:
			ExchangeAssignment.objects.filter(giftexchange=self).delete()
		new_participant, created = Participant.get_or_create(
			giftexchange=self,
			appuser=appuser,
		)
		return new_participant, created


	def _generate_assignments(self):
		starting_giver = self.participant_set.filter(status='active').order_by('?').first()
		current_giver = starting_giver

		participants = self.participant_set.filter(status='active').all()
		assignments = []
		reciever_appusers = [starting_giver.appuser, ]

		while len(assignments) <= self.participant_set.filter(status='active').all().count() - 2:
			exclusions = reciever_appusers + [current_giver.appuser]
			random_reciever_qs = self.participant_set.filter(status='active').exclude(appuser__in=exclusions)
			random_reciever = random_reciever_qs.order_by('?').first()

			if random_reciever:
				assignments.append((current_giver.appuser, random_reciever.appuser))
				reciever_appusers.append(random_reciever.appuser)
				current_giver = random_reciever

		final_giver = current_giver
		assignments.append((final_giver.appuser, starting_giver.appuser))
		return assignments

	def _verify_closed_loop(self, assignments):
		def _get_reciever_for_participant(qgiver, assignments):
			for giver, reciever in assignments:
				if giver == qgiver:
					return reciever

		# print('Checking loop is closed....')
		loop_is_closed = False
		expected_connection_count = len(assignments)
		checked_recievers = []
		first_giver = assignments[0][0]
		first_reciever = assignments[0][1]

		giver = first_giver
		reciever = first_reciever
		while first_giver not in checked_recievers:
			# print('{} gives to {}'.format(giver, reciever))
			checked_recievers.append(reciever)
			giver = reciever
			reciever = _get_reciever_for_participant(giver, assignments)

		loop_is_closed = len(checked_recievers) == expected_connection_count
		return loop_is_closed

	def generate_assignemnts(self, override_lock=False):
		if self.assignments_locked and not override_lock:
			raise Exception('Assignments are locked for this gift exchange')
		# print('Removing old assignments...')
		self.exchangeassignment_set.all().delete()
		# print('Making assignments...')
		loop_is_closed = False
		tries = 0
		while not loop_is_closed:
			assignments = self._generate_assignments()
			loop_is_closed = self._verify_closed_loop(assignments)
			tries += 1

		# print("Took {} tries".format(tries))
		assignment_objects = []
		for giver_appuser, reciever_appuser in assignments:
			giver_participant = Participant.objects.get(appuser=giver_appuser, giftexchange=self)
			reciever_participant = Participant.objects.get(appuser=reciever_appuser, giftexchange=self)
			new_assignment = ExchangeAssignment(
				giftexchange=self,
				giver=giver_participant,
				reciever=reciever_participant
			)
			new_assignment.save()
			assignment_objects.append(new_assignment)
		return assignment_objects


	def __str__(self):
		return self.title


class Participant(models.Model):
	appuser = models.ForeignKey(AppUser, on_delete=models.CASCADE)
	giftexchange = models.ForeignKey(GiftExchange, on_delete=models.CASCADE)
	status = models.CharField(
		max_length=10,
		default='invited',
		choices=[
			('invited', 'invited'),
			('declined', 'declined'),
			('active', 'active'),
		]
	)
	likes = models.TextField(blank=True, null=True)
	dislikes = models.TextField(blank=True, null=True)
	allergies_sensitivities = models.TextField(blank=True, null=True)
	shipping_address = models.TextField(blank=True, null=True)
	gift = models.TextField(blank=True, null=True)

	@property
	def get_shipping_address(self):
		return self.shipping_address or self.appuser.default_shipping_address

	def set_gift(self, gift_value):
		self.gift = gift_value
		self.save()

	def update(self, likes, dislikes, allergies_sensitivities):
		self.likes = likes
		self.dislikes = dislikes
		self.allergies_sensitivities = allergies_sensitivities
		self.save()


	@classmethod
	def get_or_create(cls, appuser, giftexchange, likes=None, dislikes=None, allergies_sensitivities=None, shipping_address=None):
		created = False
		existing_participant = cls.objects.filter(appuser=appuser, giftexchange=giftexchange).exists()
		if existing_participant:
			participant = cls.objects.get(appuser=appuser, giftexchange=giftexchange)
			created = False
		else:
			participant = cls(
				appuser=appuser,
				giftexchange=giftexchange,
				likes=appuser.default_likes,
				dislikes=appuser.default_dislikes,
				allergies_sensitivities=appuser.default_allergies_sensitivities
			)
			if likes:
				participant.likes = likes
			if dislikes:
				participant.dislikes = dislikes
			if allergies_sensitivities:
				participant.allergies_sensitivities = allergies_sensitivities
			if shipping_address:
				participant.shipping_address = shipping_address
			participant.save()
			created = True
		return participant, created

	def __str__(self):
		return '{} // {}'.format(self.giftexchange.title, self.appuser)


class ExchangeAssignment(models.Model):
	giftexchange = models.ForeignKey(GiftExchange, on_delete=models.CASCADE)
	giver = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='giftexchange_giver')
	reciever = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='giftexchange_reciever')
	email_sent = models.BooleanField(default=False)

	class Meta:
		unique_together = ['giftexchange', 'giver', 'reciever']

	def __str__(self):
		return '{} // {} -> {}'.format(self.giftexchange, self.giver, self.reciever)

	def send_assignment_email(self):
		subject = 'You have been given an assignment for "{}"'.format(self.giftexchange.title)
		formatted_body = render_to_string(
			'giftexchange/emails/assignment_email.html',
			context={
				'assignment': self.reciever,
				'giftexchange': self.giftexchange
			}
		)
		email = send_email(
		    subject=subject,
		    html_body=formatted_body,
		    to_emails=self.giver.appuser.djangouser.email,
		)
		email.content_subtype = 'html'
		self.email_sent = True
		self.save()

class AppInvitation(models.Model):
	inviter = models.ForeignKey(AppUser, related_name='inviter', on_delete=models.CASCADE)
	invitee_email = models.EmailField()
	giftexchange = models.ForeignKey(GiftExchange, on_delete=models.CASCADE)
	status = models.CharField(max_length=10, default='pending', choices=[('sent', 'sent'), ('pending', 'pending'), ('accepted', 'accepted')])

	def __str__(self):
		return 'invite to {} from {}'.format(self.invitee_email, self.inviter)

	@classmethod
	def get_or_create(cls, inviter, invitee_email, giftexchange):
		reason = None
		created = False
		instance = None
		appuser_exists = AppUser.get_by_email(invitee_email)
		if appuser_exists:
			reason = 'This user already has an account.'
			return instance, created, reason

		app_invite_exists = cls.objects.filter(
			inviter=inviter,
			invitee_email=invitee_email,
			giftexchange=giftexchange,
			status='sent'
		).exists()
		if app_invite_exists:
			reason = 'An invitation has already been sent to this user'
			return instance, created, reason

		instance = cls(
			inviter=inviter,
			invitee_email=invitee_email,
			giftexchange=giftexchange,
		)
		instance.save()
		created = True
		return instance, created, reason

	def send_invitation_for_new_user(self, magic_link):
		subject = "You have been invited you to join a gift exchange at Gifterator3000!"
		body = """
		Hello!<br /><br />
		You have been invited to join "{}" by {} {}. To accept the invitation, <a href="{}">login with this link</a>.
		"""
		formatted_body = body.format(
	    	self.giftexchange.title,
	    	self.inviter.djangouser.first_name,
	    	self.inviter.djangouser.last_name,
	    	magic_link,
	    )
		email = send_email(
		    subject=subject,
		    html_body=formatted_body,
		    to_emails=self.invitee_email,
		)
		self.status = 'sent'
		self.save()
