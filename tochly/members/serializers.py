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
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    team = serializers.PrimaryKeyRelatedField(queryset=Team.objects.all())
    tid = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Member
        fields = '__all__'

    def get_tid(self, obj):
        return obj.tid

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['user'] = UserSerializer(instance.user).data
        return representation
