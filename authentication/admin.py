from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'display_name', 'city', 'updated_at')
    list_filter = ('city',)
    search_fields = ('user__username', 'display_name')
