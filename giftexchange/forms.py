from django.forms import ModelForm, PasswordInput
from django.contrib.auth.models import User
from giftexchange.models import Participant, GiftExchange

class ParticipantDetailsForm(ModelForm):
	class Meta:
		model = Participant
		fields = ['likes', 'dislikes', 'allergies_sensitivities']


class GiftExchangeDetailsForm(ModelForm):
	class Meta:
		model = GiftExchange
		fields = ['location', 'description', 'spending_limit', 'date']


class LoginForm(ModelForm):

    class Meta:
        model = User
        fields = ['email', 'password']
        widgets = {
            'password': PasswordInput(),
        }
