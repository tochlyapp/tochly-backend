from django.db import models
from django.conf import settings


class Team(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Member(models.Model):
    PERMISSIONS = [
        ('OWNER', 'owner'),
        ('ADMIN', 'admin'),
        ('MEMBER', 'member')
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    permission = models.CharField(max_length=10, choices=PERMISSIONS, default='member')
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
