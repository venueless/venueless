# Generated by Django 4.2.13 on 2024-07-26 14:16

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0065_alter_auditlog_data_alter_chatevent_content_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="DigitalSambaCall",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4, primary_key=True, serialize=False
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                ("config", models.JSONField(default=dict)),
                ("ds_id", models.UUIDField()),
                ("url_name", models.CharField(max_length=255)),
                (
                    "invited_members",
                    models.ManyToManyField(related_name="ds_invites", to="core.user"),
                ),
                (
                    "room",
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="ds_call",
                        to="core.room",
                    ),
                ),
                (
                    "world",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="ds_calls",
                        to="core.world",
                    ),
                ),
            ],
        ),
    ]
