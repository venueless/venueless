# Generated by Django 3.0.5 on 2020-05-26 14:05

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0006_auto_20200520_2203"),
    ]

    operations = [
        migrations.AddField(
            model_name="reaction",
            name="datetime",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
    ]
