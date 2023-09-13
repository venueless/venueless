# Generated by Django 3.2.10 on 2022-01-19 16:55

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0055_world_external_auth_url"),
    ]

    operations = [
        migrations.CreateModel(
            name="Announcement",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, primary_key=True, serialize=False
                    ),
                ),
                ("text", models.TextField()),
                ("show_until", models.DateTimeField(null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "world",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="announcements",
                        to="core.world",
                    ),
                ),
            ],
        ),
    ]
