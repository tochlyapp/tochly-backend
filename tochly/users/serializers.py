from rest_framework import serializers
from djoser.serializers import UserCreateSerializer
from users.models import User, Profile

class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = tuple(UserCreateSerializer.Meta.fields)

    def perform_create(self, validated_data):
        user = super().perform_create(validated_data)
        Profile.objects.create(user=user)
        return user
    
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')


class ProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
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
            raise serializers.ValidationError({"user": "User is required"})
        return Profile.objects.create(user=user, **validated_data)
