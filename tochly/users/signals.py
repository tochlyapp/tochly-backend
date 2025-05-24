from django.dispatch import receiver
from djoser.signals import user_activated
from users.models import Profile

@receiver(user_activated)
def create_user_profile(_, user, *args, **kwargs):
    Profile.objects.create(user=user)
