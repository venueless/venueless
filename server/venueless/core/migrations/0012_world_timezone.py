# Generated by Django 3.0.6 on 2020-06-19 22:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_roomview"),
    ]

    operations = [
        migrations.AddField(
            model_name="world",
            name="timezone",
            field=models.CharField(default="Europe/Berlin", max_length=120),
        ),
    ]
