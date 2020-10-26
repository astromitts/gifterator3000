from datetime import date, datetime, timedelta
from giftexchange.models import AppUser, GiftExchange, Participant
from django.conf import settings
from giftexchange.sample_data import participant_sample

import csv


def csv_lines_to_dict(expected_header, file):

	reader = csv.DictReader(open(file, 'r'), delimiter=',', quotechar='"', skipinitialspace=True)
	dict_list = []
	if reader.fieldnames != expected_header:
		return None, 'Invalid header'
	for line in reader:
		dict_list.append(line)
	return dict_list, ''


def set_giftexchange_admin(email, giftexchange):
	appuser = AppUser.get_by_email(email)
	giftexchange.admin_appuser.add(appuser)
	giftexchange.save()
	return appuser


def create_sample_giftexchange(title=None, description=None, location=None, spending_limit=None):
	today = date.today()
	ex_date = today + timedelta(days=30)
	year = ex_date.year

	if not title:
		title = '{} Sample Gift Exchange'.format(year)
	if not description:
		description = 'This is a sample gift exchange used for testing! It happens in 30 dats! What fun!'
	if not location:
		location = 'Washington, DC'
	if not spending_limit:
		spending_limit = 25

	giftexchange, created = GiftExchange.get_or_create(title=title)

	giftexchange.description = description
	giftexchange.date = ex_date
	giftexchange.spending_limit = spending_limit
	giftexchange.location = location
	giftexchange.save()

	return giftexchange


def load_sample_participants(giftexchange):
	participants = []
	for row in participant_sample:
		name = row[0]
		email = row[1]
		likes = row[2]
		dislikes = row[3]
		allergies = row[4]

		first_name = name.split(' ')[0]
		last_name = name.split(' ')[1]

		djangouser, created = AppUser.get_or_create_djangouser(email, first_name, last_name)

		appuser, created = AppUser.get_or_create(djangouser)
		appuser.default_likes = likes
		appuser.default_allergies_sensitivities = allergies
		appuser.save()

		participant, created = Participant.get_or_create(giftexchange=giftexchange, appuser=appuser)
		participant.likes = likes
		participant.allergies_sensitivities = allergies
		participant.status = 'active'
		participant.save()
		participants.append(participant)
	return participants
