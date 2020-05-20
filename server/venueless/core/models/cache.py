from asgiref.sync import async_to_sync
from django.db import models, transaction

from venueless.core.utils.redis import aioredis


class VersionedModel(models.Model):
    version = models.PositiveIntegerField(default=1)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if "update_fields" in kwargs and "version" not in kwargs.get("update_fields"):
            kwargs["update_fields"].append("version")
        self.version += 1
        r = super().save(*args, **kwargs)
        transaction.on_commit(lambda: purge_cache(self))
        return r

    def delete(self, *args, **kwargs):
        self.version += 1
        transaction.on_commit(lambda: purge_cache(self))
        r = super().delete(*args, **kwargs)
        return r

    def touch(self):
        self.save(update_fields=["version"])


@async_to_sync
async def purge_cache(instance: VersionedModel):
    async with aioredis() as redis:
        redis.delete(f"modelcache:{instance._meta.label}:{instance.pk}:version")
