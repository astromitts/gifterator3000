# Generated by Django 3.0.6 on 2020-10-26 18:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('giftexchange', '0005_auto_20201026_1717'),
    ]

    operations = [
        migrations.AddField(
            model_name='giftexchange',
            name='ship_gifts_allowed',
            field=models.BooleanField(default=False),
        ),
    ]