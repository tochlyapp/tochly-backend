from django.contrib import admin
from django_tenants.admin import TenantAdminMixin

from teams.models import Team


@admin.register(Team)
class TeamAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = ('name', 'created', 'last_updated')
    list_filter = ('created', 'last_updated')
    search_fields = ('name',)
