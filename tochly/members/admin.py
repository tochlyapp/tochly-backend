from django.contrib import admin

from members.models import Team
from members.models import Member


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    list_filter = ('created', 'last_updated')
    search_fields = ('name',)

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'team')
    list_filter = ('created', 'last_updated')
