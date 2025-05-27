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
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.tid


class Member(models.Model):
    ROLES = [
        ('admin', 'ADMIN'),
        ('member', 'MEMBER'),
    ]

    STATUS_OPTIONS = [
        ('', ''),
        ('meeting', 'In a Meeting'),
        ('commuting', 'Commuting'),
        ('remote', 'Working Remotely'),
        ('sick', 'Sick'),
        ('leave', 'In Leave'),
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
    display_name = models.CharField(max_length=50)
    title = models.CharField(max_length=50, blank=True, null=True)
    phone_number = models.CharField(
        max_length=15, blank=True, null=True, unique=True, db_index=True,
    )
    online = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20, 
        choices=STATUS_OPTIONS, 
        default='', 
        blank=True, 
        null=True,
    )
    profile_picture_url = models.CharField(
        max_length=200, blank=True, null=True
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    @property
    def full_name(self):
        return f'{self.user.first_name} {self.user.last_name}'

    @property
    def tid(self):
      return self.team.tid
    
    def __str__(self):
        return self.tid
