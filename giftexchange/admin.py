from django.contrib import admin
from giftexchange.models import (
    GiftExchange,
    Participant,
    AppUser,
    ExchangeAssignment,
    AppInvitation,
    MagicLink
)


class ParticipantInline(admin.TabularInline):
    model = Participant
    fields = ['appuser']

class GiftExchangeAdmin(admin.ModelAdmin):
	inlines = [
		ParticipantInline,
	]
	list_display = ['title', 'date']

admin.site.register(AppUser)
admin.site.register(GiftExchange, GiftExchangeAdmin)
admin.site.register(Participant)
admin.site.register(ExchangeAssignment)
admin.site.register(AppInvitation)
admin.site.register(MagicLink)
