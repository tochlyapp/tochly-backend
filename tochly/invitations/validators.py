from typing import Literal, Annotated
from django.shortcuts import get_object_or_404

from pydantic_core import PydanticCustomError
from pydantic import (
    BaseModel, 
    EmailStr, 
    Field, 
    field_validator, 
    model_validator,
    AfterValidator,
)

from members.models import Team, Member

def validate_team_exists(tid: str) -> str:
    if not Team.objects.filter(tid=tid).exists():
        raise PydanticCustomError('team_does_not_exist', f'The team {tid} could not be found')
    return tid

Tid = Annotated[
    str,
    Field(..., min_length=9, max_length=10, pattern=r'^[a-zA-Z00-9]+$'),
    AfterValidator(validate_team_exists),
]

class SendInviteRequestValidator(BaseModel):
    tid: Tid
    invitee_email: EmailStr
    role: Literal['admin', 'member', 'Admin', 'Member']
    invited_by: int
    url: str = Field(..., max_length=300)

    @field_validator('*', mode='before')
    def strip_strings(cls, v):
        if isinstance(v, str):
            return v.strip().lower() if v.lower() in ('admin', 'member') else v.strip()
        return v

    @field_validator('invited_by')
    def validate_inviter(cls, v, info):
        team = get_object_or_404(Team, tid=info.data.get('tid', ''))
        member = get_object_or_404(Member, user_id=v, team=team)
        
        if member.role != 'admin':
            raise PydanticCustomError('member_not_an_admin', 'Inviting member must be an admin')
        return v
    
    @model_validator(mode='after')
    def validate_invitee_not_member(self):
        if Member.objects.filter(
            user__email=self.invitee_email,
            team__tid=self.tid
        ).exists():
            raise PydanticCustomError('cannot_invite_a_member', 'Invitee is already a team member')
        return self
    

class AcceptInviteValidator(SendInviteRequestValidator):
    expires_at: str
