from django.core.management.base import BaseCommand, CommandError
from giftexchange.utils import load_sample_participants, create_sample_giftexchange


class Command(BaseCommand):
	help = 'Loads sample data to database from 2019 responses'	

	def handle(self, *args, **options):
		giftexchange = create_sample_giftexchange()
		participants = load_sample_participants(giftexchange)
		self.stdout.write(
			self.style.SUCCESS(
				'{} Participant instances linked to {}'.format(
					len(participants), 
					giftexchange.title
				)
			)
		)
