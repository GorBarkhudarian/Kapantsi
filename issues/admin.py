from django.contrib import admin
from .models import Issue, IssueStatusHistory, IssueComment


class IssueStatusHistoryInline(admin.TabularInline):
    model = IssueStatusHistory
    extra = 0
    readonly_fields = ['old_status', 'new_status', 'changed_by', 'note', 'changed_at']
    can_delete = False


class IssueCommentInline(admin.TabularInline):
    model = IssueComment
    extra = 1
    readonly_fields = ['created_at']


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ['id', 'title_hy', 'category', 'status', 'area', 'upvote_count', 'created_by', 'created_at']
    list_filter = ['status', 'category', 'area', 'created_at']
    search_fields = ['title_hy', 'title_en', 'description_hy', 'location_address']
    readonly_fields = ['upvote_count', 'created_at', 'updated_at']
    list_editable = ['status']
    inlines = [IssueStatusHistoryInline, IssueCommentInline]
    fieldsets = (
        ('Content', {'fields': ('title_hy', 'title_en', 'description_hy', 'description_en', 'image')}),
        ('Classification', {'fields': ('category', 'status', 'area', 'village_name')}),
        ('Location', {'fields': ('latitude', 'longitude', 'location_address')}),
        ('Meta', {'fields': ('created_by', 'upvote_count', 'admin_notes', 'created_at', 'updated_at')}),
    )


