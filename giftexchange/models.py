from django.db import models
from django.contrib.auth.models import User


class AppUser(models.Model):
	djangouser = models.OneToOneField(User, on_delete=models.CASCADE)
	needs_password_reset = models.BooleanField(default=True)

	def __str__(self):
		return '{} {} ({})'.format(self.djangouser.first_name, self.djangouser.last_name, self.djangouser.email)

	def exchange_participant(self, giftexchange):
		participant_exists = Participant.objects.filter(appuser=self, giftexchange=giftexchange).exists()
		if participant_exists:
			return Participant.objects.get(appuser=self, giftexchange=giftexchange)
		return False

	@classmethod
	def create(cls, djangouser, needs_password_reset=True):
		appuser = cls(djangouser=djangouser, needs_password_reset=needs_password_reset)
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
			tmp_password = 'dive1766@{}'.format(email.split('@')[0])
			djangouser.set_password(tmp_password)
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



class GiftExchange(models.Model):
	title = models.CharField(max_length=300, unique=True)
	date = models.DateField(blank=True, null=True)
	location = models.CharField(max_length=500)
	description = models.TextField(blank=True, null=True)
	spending_limit = models.IntegerField(default=0)
	admin_appuser = models.ManyToManyField(AppUser)
	assignments_locked = models.BooleanField(default=False)

	def get_assignment(self, giver_appuser):
		giver_participant = Participant.objects.get(giftexchange=self, appuser=giver_appuser)
		return ExchangeAssignment.objects.filter(giftexchange=self, giver=giver_participant).first().reciever

	def lock(self):
		self.assignments_locked = True
		self.save()
	
	def unlock(self):
		self.assignments_locked = False
		self.save()

	@property
	def ordered_assignments(self):
		assignments = []
		start_assignment = self.exchangeassignment_set.order_by('pk').first()
		next_assignment = start_assignment
		next_giver = start_assignment.reciever
		while next_assignment.reciever != start_assignment.giver:
			assignments.append(next_assignment)
			next_assignment = self.exchangeassignment_set.all().get(giver=next_assignment.reciever)
			next_giver = next_assignment.reciever
		assignments.append(next_assignment)
		return assignments
	

	def update(self, date, location, description, spending_limit):
		self.date = date
		self.location = location
		self.description = description
		self.spending_limit = spending_limit
		self.save()

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


	def _generate_assignments(self):
		starting_giver = self.participant_set.order_by('?').first()
		current_giver = starting_giver

		participants = self.participant_set.all()
		assignments = []
		reciever_appusers = [starting_giver.appuser, ]

		while len(assignments) <= self.participant_set.all().count() - 2:
			exclusions = reciever_appusers + [current_giver.appuser]
			random_reciever_qs = self.participant_set.exclude(appuser__in=exclusions)
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
	likes = models.TextField(blank=True, null=True)
	dislikes = models.TextField(blank=True, null=True)
	allergies_sensitivities = models.TextField(blank=True, null=True)

	def update(self, likes, dislikes, allergies_sensitivities):
		self.likes = likes
		self.dislikes = dislikes
		self.allergies_sensitivities = allergies_sensitivities
		self.save()


	@classmethod
	def get_or_create(cls, appuser, giftexchange):
		created = False
		existing_participant = cls.objects.filter(appuser=appuser, giftexchange=giftexchange).exists()
		if existing_participant:
			participant = cls.objects.get(appuser=appuser, giftexchange=giftexchange)
			created = False
		else:
			participant = cls(appuser=appuser, giftexchange=giftexchange)
			participant.save()
			created = True
		return participant, created

	def __str__(self):
		return '{} // {}'.format(self.giftexchange.title, self.appuser)


class ExchangeAssignment(models.Model):
	giftexchange = models.ForeignKey(GiftExchange, on_delete=models.CASCADE)
	giver = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='giftexchange_giver')
	reciever = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name='giftexchange_reciever')

	class Meta:
		unique_together = ['giftexchange', 'giver', 'reciever']

	def __str__(self):
		return '{} // {} -> {}'.format(self.giftexchange, self.giver, self.reciever)
