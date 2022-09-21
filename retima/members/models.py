from django.db import models
from django.conf import settings


class Member(models.Model):
    PERMISSIONS = [
        ('OWNER', 'owner'),
        ('ADMIN', 'admin'),
        ('MEMBER', 'member')
    ]
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15, blank=True, null=True, unique=True, db_index=True)
    permission = models.CharField(max_length=10, choices=PERMISSIONS, default='member')
    created = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    @property
    def email(self):
      return self.user.email

    @property
    def full_name(self):
        return f'{user.first_name} {user.last_name}'

    def __str__(self):
        return self.full_name
