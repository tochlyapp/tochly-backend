from django.contrib import admin

from members.models import Member


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone_number')
    list_filter = ('created', 'last_updated')
    search_fields = ('full_name', 'email', 'phone')
