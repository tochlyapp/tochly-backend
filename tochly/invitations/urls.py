from django.urls import path
from .views import SendMemberInviteView, AcceptMemberInviteView

urlpatterns = [
    path('send-invite/', SendMemberInviteView.as_view(), name='send-invite'),
    path('accept-invite/', AcceptMemberInviteView.as_view(), name='accept-invite'),
]
