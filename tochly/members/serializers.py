from django.contrib.auth import get_user_model

from rest_framework import serializers

from users.serializers import UserSerializer, ProfileSerializer

from members.models import Team, Member


User = get_user_model()

class TeamSerializer(serializers.ModelSerializer):

    class Meta:
        model = Team
        fields = '__all__'


class MemberSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    team = serializers.PrimaryKeyRelatedField(read_only=True)
    tid = serializers.SerializerMethodField(read_only=True)
    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Member
        fields = '__all__'

    def get_full_name(self, obj):
        return obj.full_name

    def get_tid(self, obj):
        return obj.tid

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['user'] = UserSerializer(instance.user).data
        return representation


class MemberWithProfileSerializer(serializers.ModelSerializer):
    profile = serializers.SerializerMethodField()

    class Meta:
        model = Member
        fields = (
            'id', 
            'team', 
            'role', 
            'display_name',
            'title', 
            'phone_number', 
            'online', 
            'status', 
            'profile_picture_url',
            'created',
            'updated',
            'profile',
        )

    def get_profile(self, obj):
        return ProfileSerializer(obj.user.profile).data
