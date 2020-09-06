from django.forms import Form, ModelForm, PasswordInput, FileField
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


class GiftExchangeCreateForm(ModelForm):
	class Meta:
		model = GiftExchange
		fields = ['title', 'location', 'description', 'spending_limit', 'date']


class LoginForm(ModelForm):

    class Meta:
        model = User
        fields = ['email', 'password']
        widgets = {
            'password': PasswordInput(),
        }


class FileUploadForm(Form):
	file = FileField()
