# Generated by Django 3.1.1 on 2020-09-05 14:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('giftexchange', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='giftexchange',
            name='assignments_locked',
            field=models.BooleanField(default=False),
        ),
    ]