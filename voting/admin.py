from django.contrib import admin
from .models import Vote, BlockchainVoteLog


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'issue', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'issue__title_hy']
    readonly_fields = ['created_at']


