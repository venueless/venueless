# Generated by Django 4.2.11 on 2024-03-09 13:55

import django.db.models.deletion
from django.db import migrations, models
from py_vapid import Vapid02


def gen_keys(apps, schema_editor):
    World = apps.get_model("core", "World")
    for world in World.objects.all():
        vapid = Vapid02()
        vapid.generate_keys()
        world.vapid_private_key = vapid.private_pem().decode()
        world.vapid_public_key = vapid.public_pem().decode()
        world.save()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0066_digitalsambacall"),
    ]

    operations = [
        migrations.AddField(
            model_name="world",
            name="vapid_private_key",
            field=models.TextField(default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="world",
            name="vapid_public_key",
            field=models.TextField(default=""),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name="WebPushClient",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("endpoint", models.URLField(unique=True)),
                ("subscription", models.JSONField()),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="web_push_clients",
                        to="core.user",
                    ),
                ),
            ],
        ),
        migrations.RunPython(gen_keys, migrations.RunPython.noop),
    ]