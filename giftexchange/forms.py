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
		fields = ['likes', 'dislikes', 'allergies_sensitivities']


class GiftExchangeDetailsForm(ModelForm):
	class Meta:
		model = GiftExchange
		fields = ['location', 'description', 'spending_limit', 'date']
		widgets = {
			'date': DateInput(attrs={'class':'datepicker'}),
		}


class GiftExchangeCreateForm(ModelForm):
	class Meta:
		model = GiftExchange
		fields = ['title', 'location', 'description', 'spending_limit', 'date']
		widgets = {
			'date': DateInput(attrs={'class':'datepicker'}),
		}


class LoginForm(ModelForm):

    class Meta:
        model = User
        fields = ['email', 'password']
        widgets = {
            'password': PasswordInput(),
        }


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


class PasswordChangeForm(Form):
	current_password = CharField(widget=PasswordInput())
	new_password = CharField(widget=PasswordInput())
	confirm_new_password = CharField(widget=PasswordInput())


class PasswordResetForm(Form):
	email = EmailField()
	current_password = CharField(widget=PasswordInput())
	new_password = CharField(widget=PasswordInput())
	confirm_new_password = CharField(widget=PasswordInput())


class RegisterForm(Form):
	email = EmailField()
	first_name = CharField()
	last_name = CharField()
	password = CharField(widget=PasswordInput())
	confirm_password = CharField(widget=PasswordInput())


class FileUploadForm(Form):
	file = FileField()


class ParticipantSearchForm(Form):
	email = CharField(required=False)
	first_name = CharField(required=False)
	last_name = CharField(required=False)


class EmailForm(Form):
	email = CharField(required=True)
