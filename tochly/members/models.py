from django.db import models
from django.conf import settings

from members.utils import generate_team_id


class Team(models.Model):
    name = models.CharField(max_length=50, unique=True, db_index=True)
    tid = models.CharField(
        max_length=10, unique=True, db_index=True, default=generate_team_id,
    )
    description = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.tid


class Member(models.Model):
    ROLES = [
        ('owner', 'OWNER'),
        ('admin', 'ADMIN'),
        ('member', 'MEMBER'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        related_name='members', 
        on_delete=models.CASCADE,
    )
    team = models.ForeignKey(
        Team, related_name='members', on_delete=models.CASCADE
    )
    role = models.CharField(
        max_length=10, choices=ROLES, default='member',
    )
    is_active = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def tid(self):
      return self.team.tid
