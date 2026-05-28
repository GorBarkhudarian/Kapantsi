from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from .models import User, AboutSection

admin.site.unregister(Group)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = [
        'username', 'email', 'first_name', 'last_name',
        'role', 'verified', 'doc_type', 'national_id', 'is_staff',
    ]
    list_filter = ['role', 'verified', 'doc_type', 'is_staff', 'is_active']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'national_id']
    fieldsets = UserAdmin.fieldsets + (
        ('Kapantsi Profile', {
            'fields': ('role', 'doc_type', 'national_id', 'verified', 'phone', 'address', 'avatar'),
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Kapantsi Profile', {
            'fields': ('role', 'doc_type', 'national_id', 'verified', 'phone', 'address'),
        }),
    )


@admin.register(AboutSection)
class AboutSectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'language', 'order', 'is_active', 'updated_at']
    list_filter = ['language', 'is_active']
    list_editable = ['order', 'is_active']
    search_fields = ['title', 'body']
    ordering = ['language', 'order']
    fieldsets = (
        (None, {
            'fields': ('language', 'order', 'is_active'),
        }),
        ('Content', {
            'fields': ('title', 'body'),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ['created_at', 'updated_at']
