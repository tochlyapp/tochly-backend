from django.contrib.auth import get_user_model
from rest_framework import serializers

from users.serializers import ProfileSerializer, CustomUserCreateSerializer
from members.models import Team, Member

User = get_user_model()

class TeamSerializer(serializers.ModelSerializer):

    class Meta:
        model = Team
        fields = '__all__'


class MemberSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField(read_only=True)
    tid = serializers.SerializerMethodField(read_only=True)
    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Member
        fields = (
            'id',
            'user',
            'profile',
            'team',
            'tid',
            'full_name',
            'role',
            'display_name',
            'title',
            'phone_number',
            'online',
            'status',
            'profile_picture_url',
            'created',
            'updated',
        )
        read_only_fields = ('id', 'team')

    def get_user(self, obj):
        return CustomUserCreateSerializer(obj.user).data

    def get_profile(self, obj):
        return ProfileSerializer(obj.user.profile).data

    def get_tid(self, obj):
        return obj.tid
    
    def get_full_name(self, obj):
        return obj.full_name
