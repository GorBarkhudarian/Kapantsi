from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from .models import Issue, IssueStatusHistory, IssueComment
from accounts.serializers import UserSerializer


class IssueCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.SerializerMethodField()

    class Meta:
        model = IssueComment
        fields = ['id', 'author', 'author_name', 'body', 'created_at']
        read_only_fields = ['author', 'created_at']

    def get_author_name(self, obj):
        if obj.author:
            return obj.author.get_full_name() or obj.author.username
        return 'Unknown'


class IssueStatusHistorySerializer(serializers.ModelSerializer):
    changed_by_name = serializers.SerializerMethodField()
    old_status_display = serializers.SerializerMethodField()
    new_status_display = serializers.SerializerMethodField()

    class Meta:
        model = IssueStatusHistory
        fields = ['id', 'old_status', 'old_status_display', 'new_status',
                  'new_status_display', 'changed_by_name', 'note', 'changed_at']

    def get_changed_by_name(self, obj):
        if obj.changed_by:
            return obj.changed_by.get_full_name() or obj.changed_by.username
        return 'System'

    def get_old_status_display(self, obj):
        return dict(Issue.STATUS_CHOICES).get(obj.old_status, obj.old_status)

    def get_new_status_display(self, obj):
        return dict(Issue.STATUS_CHOICES).get(obj.new_status, obj.new_status)


class IssueListSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    category_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    user_voted = serializers.SerializerMethodField()
    comments_count = serializers.SerializerMethodField()
    first_image = serializers.SerializerMethodField()

    class Meta:
        model = Issue
        fields = ['id', 'title_hy', 'title_en', 'category', 'category_display',
                  'status', 'status_display', 'area', 'village_name',
                  'latitude', 'longitude', 'location_address',
                  'upvote_count', 'comments_count', 'created_by_name', 'created_at', 'image', 'first_image', 'user_voted']

    def get_first_image(self, obj):
        request = self.context.get('request')
        if obj.image:
            url = obj.image.url
            return request.build_absolute_uri(url) if request else url
        first = obj.extra_images.first()
        if first:
            url = first.image.url
            return request.build_absolute_uri(url) if request else url
        return None

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return 'Anonymous'

    def get_category_display(self, obj):
        return obj.get_category_display()

    def get_status_display(self, obj):
        return obj.get_status_display()

    def get_user_voted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.votes.filter(user=request.user).exists()
        return False

    def get_comments_count(self, obj):
        return obj.comments.count()


class IssueDetailSerializer(IssueListSerializer):
    comments = IssueCommentSerializer(many=True, read_only=True)
    status_history = IssueStatusHistorySerializer(many=True, read_only=True)

    class Meta(IssueListSerializer.Meta):
        fields = IssueListSerializer.Meta.fields + [
            'description_hy', 'description_en', 'admin_notes',
            'comments', 'status_history', 'updated_at'
        ]


class IssueCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = ['title_hy', 'title_en', 'description_hy', 'description_en',
                  'category', 'area', 'village_name', 'latitude', 'longitude',
                  'location_address', 'image']

    def create(self, validated_data):
        user = self.context['request'].user
        issue = Issue.objects.create(created_by=user, **validated_data)
        return issue


class IssueStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Issue
        fields = ['status', 'admin_notes']

    def update(self, instance, validated_data):
        old_status = instance.status
        new_status = validated_data.get('status', instance.status)
        instance = super().update(instance, validated_data)
        if old_status != new_status:
            from .utils import record_status_change
            record_status_change(instance, old_status, new_status,
                                 self.context['request'].user)
        return instance
