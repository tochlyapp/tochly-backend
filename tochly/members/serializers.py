from django.contrib.auth import get_user_model

from rest_framework import serializers

from users.serializers import UserSerializer

from members.models import Team, Member


User = get_user_model()

class TeamSerializer(serializers.ModelSerializer):

    class Meta:
        model = Team
        fields = '__all__'


class MemberSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    team = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Member
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['user'] = UserSerializer(instance.user).data
        return representation
