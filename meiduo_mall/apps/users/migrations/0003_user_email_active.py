# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2019-05-16 10:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20190509_0817'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email_active',
            field=models.BooleanField(default=False, verbose_name='邮件激活状态'),
        ),
    ]