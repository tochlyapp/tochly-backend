from django.contrib import admin

from members.models import Team
from members.models import Member


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    list_filter = ('created', 'updated')
    search_fields = ('name',)

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = (
        'user', 
        'team',
        'display_name', 
        'title', 
        'phone_number', 
        'online', 
        'status', 
        'profile_picture_url',
    )
    list_filter = ('created', 'updated')
    search_fields = ('display_name', 'title')
