from django.core.management.base import BaseCommand, CommandError

from giftexchange.models import GiftExchange


class Command(BaseCommand):
	help = 'Generates exchange assignments for given Gift Exchange ID'
	
	def add_arguments(self, parser):
		parser.add_argument('id', type=int)
	
	def handle(self, *args, **options):
		try:
			giftexchange = GiftExchange.objects.get(pk=options['id'])
		except GiftExchange.DoesNotExist:
			raise CommandError('GiftExchange "{}" does not exist'.format(options['id']))
		giftexchange.assignments_locked = False
		giftexchange.save()
		self.stdout.write(self.style.SUCCESS('Assignments unlocked for GiftExchange "{}"'.format(giftexchange.title))) 