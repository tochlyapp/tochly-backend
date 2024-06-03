from rest_framework import serializers

from members.models import Team, Member


class TeamSerializer(serializers.ModelSerializer):

    class Meta:
        model = Team
        fields = "__all__"


class MemberSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    team = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Member
        fields = "__all__"
