from django.forms import (
	Form,
	ModelForm,
	PasswordInput,
	FileField,
	DateInput,
	EmailField,
	CharField,
	Textarea,
	HiddenInput,
)
from django.contrib.auth.models import User
from giftexchange.models import Participant, GiftExchange


class ParticipantDetailsForm(ModelForm):
	class Meta:
		model = Participant
		fields = ['first_name', 'last_name', 'email', 'likes', 'dislikes', 'allergies_sensitivities', 'shipping_address', 'additional_info']


class GiftExchangeDetailsForm(ModelForm):
	class Meta:
		model = GiftExchange
		fields = ['location', 'description', 'spending_limit', 'date', 'ship_gifts_allowed']
		widgets = {
			'date': DateInput(attrs={'class':'datepicker'}),
		}


class GiftExchangeCreateForm(ModelForm):
	class Meta:
		model = GiftExchange
		fields = ['title', 'location', 'description', 'spending_limit', 'date', 'ship_gifts_allowed']
		widgets = {
			'date': DateInput(attrs={'class':'datepicker'}),
		}


class LoginForm(ModelForm):

    class Meta:
        model = User
        fields = ['email']


class GiftForm(ModelForm):
	class Meta:
		model = Participant
		fields = ['gift']


class ProfileForm(Form):
	first_name = CharField()
	last_name = CharField()
	email = EmailField()
	default_likes = CharField(widget=Textarea, required=False)
	default_dislikes = CharField(widget=Textarea, required=False)
	default_allergies_and_sensitivites = CharField(widget=Textarea, required=False)
	default_shipping_address = CharField(widget=Textarea, required=False)
	default_additional_info = CharField(widget=Textarea, required=False)


class RegisterForm(Form):
	email = EmailField()
	first_name = CharField()
	last_name = CharField()


class FileUploadForm(Form):
	file = FileField()


class ParticipantSearchForm(Form):
	email = CharField(required=False)
	first_name = CharField(required=False)
	last_name = CharField(required=False)


class EmailForm(Form):
	email = CharField(required=True)
