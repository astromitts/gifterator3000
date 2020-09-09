# Generated by Django 3.1.1 on 2020-09-08 23:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


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
                ('needs_password_reset', models.BooleanField(default=True)),
                ('default_likes', models.TextField(blank=True, null=True)),
                ('default_dislikes', models.TextField(blank=True, null=True)),
                ('default_allergies_sensitivities', models.TextField(blank=True, null=True)),
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
                ('admin_appuser', models.ManyToManyField(to='giftexchange.AppUser')),
            ],
        ),
        migrations.CreateModel(
            name='Participant',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('invited', 'invited'), ('declined', 'declined'), ('active', 'active')], default='invited', max_length=10)),
                ('likes', models.TextField(blank=True, null=True)),
                ('dislikes', models.TextField(blank=True, null=True)),
                ('allergies_sensitivities', models.TextField(blank=True, null=True)),
                ('gift', models.TextField(blank=True, null=True)),
                ('appuser', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='giftexchange.appuser')),
                ('giftexchange', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='giftexchange.giftexchange')),
            ],
        ),
        migrations.CreateModel(
            name='AppInvitation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invitee_email', models.EmailField(max_length=254)),
                ('status', models.CharField(choices=[('sent', 'sent'), ('pending', 'pending')], default='pending', max_length=10)),
                ('giftexchange', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='giftexchange.giftexchange')),
                ('inviter', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inviter', to='giftexchange.appuser')),
            ],
        ),
        migrations.CreateModel(
            name='ExchangeAssignment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('giftexchange', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='giftexchange.giftexchange')),
                ('giver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='giftexchange_giver', to='giftexchange.participant')),
                ('reciever', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='giftexchange_reciever', to='giftexchange.participant')),
            ],
            options={
                'unique_together': {('giftexchange', 'giver', 'reciever')},
            },
        ),
    ]
