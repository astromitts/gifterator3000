from django.forms import ModelForm

from giftexchange.models import Participant, GiftExchange

class ParticipantDetailsForm(ModelForm):
	class Meta:
		model = Participant
		fields = ['likes', 'dislikes', 'allergies_sensitivities']


class GiftExchangeDetailsForm(ModelForm):
	class Meta:
		model = GiftExchange
		fields = ['location', 'description', 'spending_limit', 'date']
