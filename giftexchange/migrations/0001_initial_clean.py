# Generated by Django 3.0.6 on 2020-10-27 15:58

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import giftexchange.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AppUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('default_likes', models.TextField(blank=True, null=True)),
                ('default_dislikes', models.TextField(blank=True, null=True)),
                ('default_allergies_sensitivities', models.TextField(blank=True, null=True)),
                ('default_shipping_address', models.TextField(blank=True, null=True)),
                ('djangouser', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='GiftExchange',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=300, unique=True)),
                ('date', models.DateField(blank=True, null=True)),
                ('location', models.CharField(max_length=500)),
                ('description', models.TextField(blank=True, null=True)),
                ('spending_limit', models.IntegerField(default=0)),
                ('assignments_locked', models.BooleanField(default=False)),
                ('ship_gifts_allowed', models.BooleanField(default=False)),
                ('admin_appuser', models.ManyToManyField(to='giftexchange.AppUser')),
            ],
        ),
        migrations.CreateModel(
            name='MagicLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('expiration', models.DateTimeField(default=giftexchange.models.twentyfourhoursfromnow)),
                ('user_email', models.EmailField(max_length=254)),
                ('token', models.CharField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='Participant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('invited', 'invited'), ('declined', 'declined'), ('active', 'active')], default='invited', max_length=10)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('email', models.EmailField(max_length=254)),
                ('likes', models.TextField(blank=True, null=True)),
                ('dislikes', models.TextField(blank=True, null=True)),
                ('allergies_sensitivities', models.TextField(blank=True, null=True)),
                ('shipping_address', models.TextField(blank=True, null=True)),
                ('gift', models.TextField(blank=True, null=True)),
                ('giftexchange', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='giftexchange.GiftExchange')),
            ],
        ),
        migrations.CreateModel(
            name='AppInvitation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invitee_email', models.EmailField(blank=True, max_length=254, null=True)),
                ('status', models.CharField(choices=[('sent', 'sent'), ('pending', 'pending'), ('accepted', 'accepted')], default='pending', max_length=10)),
                ('giftexchange', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='giftexchange.GiftExchange')),
                ('invitee', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='invitee', to='giftexchange.AppUser')),
                ('inviter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inviter', to='giftexchange.AppUser')),
            ],
        ),
        migrations.CreateModel(
            name='AdminInvitation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('sent', 'sent'), ('pending', 'pending'), ('accepted', 'accepted')], default='pending', max_length=10)),
                ('giftexchange', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='giftexchange.GiftExchange')),
                ('inviter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='giftexchange.AppUser')),
                ('magic_link', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='giftexchange.MagicLink')),
                ('participant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='giftexchange.Participant')),
            ],
        ),
        migrations.CreateModel(
            name='ExchangeAssignment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_sent', models.BooleanField(default=False)),
                ('giftexchange', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='giftexchange.GiftExchange')),
                ('giver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='giftexchange_giver', to='giftexchange.Participant')),
                ('reciever', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='giftexchange_reciever', to='giftexchange.Participant')),
            ],
            options={
                'unique_together': {('giftexchange', 'giver', 'reciever')},
            },
        ),
    ]
