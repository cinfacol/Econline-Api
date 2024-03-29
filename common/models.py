import uuid

from django.db import models


class TimeStampedUUIDModel(models.Model):
    pkid = models.BigAutoField(primary_key=True, editable=False)
    id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class IsActiveQueryset(models.QuerySet):
    def is_active(self):
        return self.filter(is_active=True)


class PublishedManager(models.Manager):
    def get_queryset(self):
        return (
            super(PublishedManager, self).get_queryset().filter(published_status=True)
        )
