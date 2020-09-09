from django.core.management.base import BaseCommand, CommandError
from datetime import date, timedelta
from giftexchange.sample_data import participant_sample

from giftexchange.models import AppUser, Participant, GiftExchange


class Command(BaseCommand):
	help = 'Loads sample data to database from 2019 responses'	
	
	def add_arguments(self, parser):
		parser.add_argument('password', type=str)

	def handle(self, *args, **options):
		today = date.today()
		ex_date = today + timedelta(days=30)
		year = ex_date.year

		giftexchange, created = GiftExchange.get_or_create(title='{} ID Gift Exchange'.format(year))

		giftexchange.description = 'Get a flat rate shipping box and send it to some one!'
		giftexchange.date = ex_date
		giftexchange.spending_limit = 25
		giftexchange.location = 'Google Hangout'
		giftexchange.save()
		if created:
			self.stdout.write(self.style.SUCCESS('Created sample GiftExchange instance'))
		else:
			self.stdout.write(self.style.SUCCESS('Found sample GiftExchange instance'))


		appuser_count = 0
		djangouser_count = 0
		participant_count = 0
		exchange_admin = None
		for row in participant_sample:
			name = row[0]
			in_office = row[1]
			allergies = row[2]
			likes = row[3]
			email = row[4]

			first_name = name.split(' ')[0]
			last_name = name.split(' ')[1]

			djangouser, created = AppUser.get_or_create_djangouser(email, first_name, last_name)
			if created:
				djangouser_count += 1

			appuser, created = AppUser.get_or_create(djangouser)
			appuser.default_likes = likes
			appuser.default_allergies_sensitivities = allergies
			appuser.save()
			if created:
				appuser_count += 1
			if email.startswith('bmorin'):
				exchange_admin = appuser
				giftexchange.admin_appuser.add(exchange_admin)
				giftexchange.save()
				djangouser.set_password(options['password'])
				djangouser.save()
				appuser.needs_password_reset = False
				appuser.save()

			participant, created = Participant.get_or_create(giftexchange=giftexchange, appuser=appuser)
			participant.likes = likes
			participant.allergies_sensitivities = allergies
			participant.status = 'active'
			participant.save()
			if created:
				participant_count += 1


		self.stdout.write(self.style.SUCCESS('Created {} new AppUser instances'.format(appuser_count)))
		self.stdout.write(self.style.SUCCESS('Created {} new DjangoUser instances'.format(djangouser_count)))
		self.stdout.write(self.style.SUCCESS('Created {} Participant instances'.format(participant_count)))
