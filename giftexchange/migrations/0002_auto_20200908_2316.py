# Generated by Django 3.1.1 on 2020-09-08 23:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('giftexchange', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appinvitation',
            name='status',
            field=models.CharField(choices=[('sent', 'sent'), ('pending', 'pending'), ('accepted', 'accepted')], default='pending', max_length=10),
        ),
    ]