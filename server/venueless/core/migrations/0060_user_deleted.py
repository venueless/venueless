# Generated by Django 3.2.15 on 2022-08-09 19:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0059_user_pretalx_id"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="deleted",
            field=models.BooleanField(default=False),
        ),
    ]
