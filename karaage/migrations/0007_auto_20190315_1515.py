# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-03-15 15:15
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("karaage", "0006_auto_20180302_1735"),
    ]

    operations = [
        migrations.AlterField(
            model_name="person",
            name="full_name",
            field=models.CharField(max_length=100),
        ),
        migrations.AlterField(
            model_name="person",
            name="short_name",
            field=models.CharField(max_length=100),
        ),
    ]
