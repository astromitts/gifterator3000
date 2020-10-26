from django.core.management.base import BaseCommand, CommandError

from giftexchange.models import GiftExchange


class Command(BaseCommand):
	help = 'Lists gift exchanges and IDs'
	
	def handle(self, *args, **options):
		giftexchanges = GiftExchange.objects.order_by('pk').all()
		for giftexchange in giftexchanges:
			self.stdout.write('PK: {} // TITLE: "{}"'.format(giftexchange.pk, giftexchange.title))
			