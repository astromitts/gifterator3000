# Generated by Django 3.0.6 on 2020-12-04 00:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('giftexchange', '0003_auto_20201204_0042'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='appuser',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='giftexchange.AppUser'),
        ),
    ]
