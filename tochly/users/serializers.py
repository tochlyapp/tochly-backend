import pytz
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as BaseUserCreateSerializer

from users.models import User, Profile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'timezone')
        read_only_fields = ('id', 'email')

class CustomUserCreateSerializer(BaseUserCreateSerializer):
    timezone = serializers.ChoiceField(choices=[(tz, tz) for tz in pytz.all_timezones], required=False)
    re_password = serializers.CharField(write_only=True)

    class Meta(BaseUserCreateSerializer.Meta):
        model = User
        fields = (
            'id',
            'email',
            'first_name',
            'last_name',
            'password',
            're_password',
            'timezone',
        )
        extra_kwargs = {
        'id': {'read_only': True},
        'password': {'write_only': True},
        're_password': {'write_only': True}
    }

class ProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    email = serializers.SerializerMethodField(read_only=True)
    full_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Profile
        fields = '__all__'

    def get_full_name(self, obj):
        return obj.full_name

    def get_email(self, obj):
        return obj.email

    def create(self, validated_data):
        user = validated_data.pop('user', None)
        if not user:
            raise serializers.ValidationError({'user': 'User is required'})
        return Profile.objects.create(user=user, **validated_data)
