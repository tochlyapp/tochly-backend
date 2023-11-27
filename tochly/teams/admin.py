from django.contrib import admin

from teams.models import Team


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'created', 'last_updated')
    list_filter = ('created', 'last_updated')
    search_fields = ('name',)
