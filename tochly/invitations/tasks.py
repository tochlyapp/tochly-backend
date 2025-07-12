from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_member_invite_email(to_email, team_name, invite_link):
    subject = f"You're invited to join {team_name} on Tochly"
    message = f"Hi,\n\nYou've been invited to join {team_name}.\nAccept the invite here: {invite_link}\n\nThanks!"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to_email])
