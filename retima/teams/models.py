from django.db import models
from django.conf import settings
from django_tenants.models import TenantMixin, DomainMixin


class Team(TenantMixin):
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='teams')
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)


class Domain(DomainMixin):
    pass
