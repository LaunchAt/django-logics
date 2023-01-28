import datetime
import logging
from typing import Type, TypeVar, Optional
from uuid import UUID

import jsonschema
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.db.models import Model as DjangoModel
from django.db.models.query import QuerySet as DjangoQuerySet
from django.utils.timezone import now

from .models import Invitation as BaseInvitation
from .models import InvitationStatus
from .models import Member as BaseMember
from .models import Organization as BaseOrganization
from .models import PermissionLevel

logger = logging.getLogger(__name__)


# Types

User = TypeVar('User', bound=DjangoModel)


# schema

PERMISSIONS_POLICY_SCHEMA = {
    'type': 'object',
    'properties': {
        'version': {'type': 'number'},
        'statement': {
            'type': 'object',
            'additionalProperties': {
                'anyOf': [
                    {'type': 'string'},
                    {'type': 'number'},
                ],
            },
        },
    },
    'required': ['version'],
}


# exception


class OrganizationServiceException(Exception):
    code = ''

    def __init__(self, *args, code='', message='', object=None) -> None:
        self.code = code
        super().__init__(*args)


# Service


class OrganizationService:
    DEFAULT_PERMISSIONS_POLICY = { 'version': 0 }

    def __init__(
        self: 'OrganizationService',
        *,
        invitation_class: Optional[Type[BaseInvitation]] = None,
        member_class: Optional[Type[BaseMember]] = None,
        organization_class: Optional[Type[BaseOrganization]] = None,
        user_class: Optional[Type[User]] = None,
    ) -> None:
        if (
            invitation_class is None
            or member_class is None
            or organization_class is None
            or user_class is None
            or not issubclass(invitation_class, BaseInvitation)
            or not issubclass(member_class, BaseMember)
            or not issubclass(organization_class, BaseOrganization)
            or not issubclass(user_class, DjangoModel)
        ):
            raise ValueError

        self._invitation_model = invitation_class
        self._member_model = member_class
        self._organization_model = organization_class
        self._user_model = user_class

    def _validate_permissions_policy(
        self: 'OrganizationService',
        *,
        permissions_policy: Optional[dict] = None,
    ) -> None:
        if permissions_policy is None:
            raise ValueError

        try:
            jsonschema.validate(
                instance=permissions_policy,
                schema=PERMISSIONS_POLICY_SCHEMA,
            )

        except jsonschema.ValueError:
            raise ValueError

    def _validate_instances(
        self: 'OrganizationService',
        *,
        id: Optional[str] = None,
        invitation: Optional[BaseInvitation] = None,
        member: Optional[BaseMember] = None,
        organization: Optional[BaseOrganization] = None,
        user: Optional[User] = None,
    ) -> None:
        if invitation is not None:
            if not isinstance(invitation, self._invitation_model):
                raise ValueError

        if member is not None:
            if not isinstance(member, self._member_model):
                raise ValueError

        if organization is not None:
            if not isinstance(organization, self._organization_model):
                raise ValueError

        if user is not None:
            if not isinstance(user, self._user_model):
                raise ValueError

        if id is not None:
            if not isinstance(id, str):
                raise ValueError

    def _check_user_permission(
        self: 'OrganizationService',
        *,
        action: Optional[str] = None,
        organization: Optional[BaseOrganization] = None,
        user: Optional[User] = None,
    ) -> bool:
        if not action or organization is None or user is None:
            raise ValueError

        permissions_policy = organization.permissions_policy or {'version': 0}
        self._validate_permissions_policy(permissions_policy=permissions_policy)
        version = permissions_policy.get('version', 0)
        kwargs = {'user_id': user.id, 'organization_id': organization.id}

        if version == 0:
            kwargs[
                'permission_level__gte'
            ] = PermissionLevel.OWNER.value  # type: ignore
            queryset = self._member_model.objects.filter(**kwargs)

            if not queryset.exists():
                raise PermissionDenied

        elif version == 1:
            statement = permissions_policy.get('statement', {})

            if action in statement:
                permission_level = statement.get(action)

                if permission_level != 0:
                    kwargs['permission_level__gte'] = permission_level
                    queryset = self._member_model.objects.filter(**kwargs)

                    if not queryset.exists():
                        raise PermissionDenied

        else:
            raise PermissionDenied

    def get_organization_set(
        self: 'OrganizationService',
    ) -> DjangoQuerySet[BaseOrganization]:
        queryset = self._organization_model.objects.all()
        queryset = queryset.select_related('owner', 'super_organization')
        queryset = queryset.prefetch_related(
            'member_set',
            'invitation_set',
            'sub_organization_set',
        )
        return queryset

    def get_sub_organization_set(
        self: 'OrganizationService',
        *,
        organization: Optional[BaseOrganization] = None,
        request_user: Optional[User] = None,
    ) -> DjangoQuerySet[BaseOrganization]:
        if organization is None or request_user is None:
            raise ValueError

        self._validate_instances(organization=organization, user=request_user)
        self._check_user_permission(
            action='get_sub_organization_set',
            organization=organization,
            user=request_user,
        )
        queryset = self._organization_model.objects.all()
        queryset = queryset.filter(super_organization_id=organization.id)
        queryset = queryset.select_related('owner', 'super_organization')
        queryset = queryset.prefetch_related(
            'member_set',
            'invitation_set',
            'sub_organization_set',
        )
        return queryset

    def get_organization(
        self: 'OrganizationService',
        *,
        id: Optional[str] = None,
        request_user: Optional[User] = None,
    ) -> Optional[BaseOrganization]:
        if id is None or request_user is None:
            raise ValueError

        self._validate_instances(user=request_user, id=id)
        queryset = self._organization_model.objects.all()
        queryset = queryset.filter(id=UUID(id))
        queryset = queryset.select_related('owner', 'super_organization')
        queryset = queryset.prefetch_related(
            'member_set',
            'invitation_set',
            'sub_organization_set',
        )

        try:
            organization = queryset.get()
            return organization

        except ObjectDoesNotExist:
            return None

    def update_organization_policy(
        self: 'OrganizationService',
        *,
        permissions_policy: Optional[dict] = None,
        organization: Optional[BaseOrganization] = None,
        request_user: Optional[User] = None,
    ) -> BaseOrganization:
        if organization is None or request_user is None:
            raise ValueError

        self._validate_instances(organization=organization, user=request_user)
        self._check_user_permission(
            action='update_organization_policy',
            organization=organization,
            user=request_user,
        )
        self._validate_permissions_policy(permissions_policy=permissions_policy)
        organization.permissions_policy = permissions_policy
        organization.save(update_fields=['permissions_policy'])
        return organization

    def create_organization(
        self: 'OrganizationService',
        *,
        request_user: Optional[User] = None,
    ) -> BaseOrganization:
        if request_user is None:
            raise ValueError

        self._validate_instances(user=request_user)
        self._validate_permissions_policy(
            permissions_policy=self.DEFAULT_PERMISSIONS_POLICY,
        )
        organization = self._organization_model.objects.create(
            owner_id=request_user.id,
            permissions_policy=self.DEFAULT_PERMISSIONS_POLICY,
        )
        return organization

    def create_sub_organization(
        self: 'OrganizationService',
        *,
        organization: Optional[BaseOrganization] = None,
        request_user: Optional[User] = None,
    ) -> BaseOrganization:
        if organization is None or request_user is None:
            raise ValueError

        self._validate_instances(organization=organization, user=request_user)
        self._check_user_permission(
            action='create_sub_organization',
            organization=organization,
            user=request_user,
        )
        kwargs = {'owner_id': request_user.id, 'super_organization_id': organization.id}
        sub_organization = self._organization_model.objects.create(**kwargs)
        return sub_organization

    def delete_organization(
        self: 'OrganizationService',
        *,
        organization: Optional[BaseOrganization] = None,
        request_user: Optional[User] = None,
    ) -> BaseOrganization:
        if organization is None or request_user is None:
            raise ValueError

        self._validate_instances(organization=organization, user=request_user)
        self._check_user_permission(
            action='delete_organization',
            organization=organization,
            user=request_user,
        )

        organization.delete()
        return organization

    def get_invitation_set(
        self: 'OrganizationService',
        *,
        organization: Optional[BaseOrganization] = None,
        request_user: Optional[User] = None,
    ) -> DjangoQuerySet[BaseInvitation]:
        if organization is None and request_user is None:
            return self._invitation_model.objects.none()

        if organization is not None:
            self._validate_instances(organization=organization, user=request_user)
            self._check_user_permission(
                action='get_invitation_set',
                organization=organization,
                user=request_user,
            )
            queryset = self._invitation_model.objects.all()
            queryset = queryset.filter(organization_id=organization.id)

        else:
            self._validate_instances(user=request_user)
            queryset = self._invitation_model.objects.all()
            queryset = queryset.filter(email=request_user.email)

        queryset = queryset.filter(expires_at__gt=now())
        queryset = queryset.filter(
            status=InvitationStatus.PENDING.value,  # type: ignore
        )
        queryset = queryset.select_related('inviter', 'member', 'organization')
        return queryset

    def get_invitation(
        self: 'OrganizationService',
        *,
        id: Optional[str] = None,
        organization: Optional[BaseOrganization] = None,
        request_user: Optional[User] = None,
        queryset: Optional[DjangoQuerySet[BaseInvitation]] = None,
    ) -> Optional[BaseInvitation]:
        if id is None or request_user is None:
            raise ValueError

        self._validate_instances(organization=organization, user=request_user, id=id)

        if queryset is not None:
            invitation_set = queryset

        elif organization is not None:
            invitation_set = self._invitation_model.objects.all()
            invitation_set = invitation_set.filter(organization_id=organization.id)

        else:
            invitation_set = self._invitation_model.objects.all()
            invitation_set = invitation_set.filter(email=request_user.email)

        invitation_set = invitation_set.filter(expires_at__gt=now())
        invitation_set = invitation_set.filter(id=UUID(id))
        invitation_set = invitation_set.filter(
            status=InvitationStatus.PENDING.value,  # type: ignore
        )
        invitation_set = invitation_set.select_related(
            'inviter',
            'organization',
            'member',
        )

        try:
            return invitation_set.get()

        except ObjectDoesNotExist:
            return None

    def create_invitation(
        self: 'OrganizationService',
        *,
        email: Optional[str] = None,
        expires_at: Optional[datetime.date] = None,
        organization: Optional[BaseOrganization] = None,
        permission_level: Optional[int] = None,
        request_user: Optional[User] = None,
    ) -> BaseInvitation:
        if (
            email is None
            or expires_at is None
            or organization is None
            or request_user is None
        ):
            raise ValueError

        self._validate_instances(organization=organization, user=request_user)

        if self._invitation_model.objects.filter(
            organization=organization,
            email=email,
        ).exists():
            raise OrganizationServiceException(code='already_invited')

        if self._member_model.objects.filter(
            organization=organization,
            user__email=email,
        ).exists():
            raise OrganizationServiceException(code='already_joined')

        self._check_user_permission(
            action='create_invitation',
            organization=organization,
            user=request_user,
        )
        kwargs = {
            'email': email,
            'expires_at': expires_at,
            'inviter_id': request_user.id,
            'organization_id': organization.id,
        }

        if permission_level:
            kwargs['permission_level'] = permission_level

        invitaiton = self._invitation_model.objects.create(**kwargs)
        return invitaiton

    def update_invitation_permission(
        self: 'OrganizationService',
        *,
        invitation: Optional[BaseInvitation] = None,
        permission_level: Optional[int] = None,
        request_user: Optional[User] = None,
    ) -> BaseInvitation:
        if (
            invitation is None
            or request_user is None
            or not isinstance(permission_level, int)
        ):
            raise ValueError

        self._validate_instances(invitation=invitation, user=request_user)

        if invitation.status != InvitationStatus.PENDING.value:  # type: ignore
            raise ValueError

        self._check_user_permission(
            action='update_invitation_permission',
            organization=invitation.organization,
            user=request_user,
        )

        invitation.permission_level = permission_level
        invitation.save(update_fields=['permission_level'])
        return invitation

    def cancel_invitation(
        self: 'OrganizationService',
        *,
        invitation: Optional[BaseInvitation] = None,
        request_user: Optional[User] = None,
    ) -> BaseInvitation:
        if invitation is None or request_user is None:
            raise ValueError

        self._validate_instances(invitation=invitation, user=request_user)

        if invitation.status != InvitationStatus.PENDING.value:  # type: ignore
            raise ValueError

        self._check_user_permission(
            action='cancel_invitation',
            organization=invitation.organization,
            user=request_user,
        )

        invitation.status = InvitationStatus.CANCELED.value  # type: ignore
        invitation.save(update_fields=['status'])
        return invitation

    def accept_invitation(
        self: 'OrganizationService',
        *,
        invitation: Optional[BaseInvitation] = None,
        request_user: Optional[User] = None,
    ) -> BaseMember:
        if invitation is None or request_user is None:
            raise ValueError

        self._validate_instances(invitation=invitation, user=request_user)

        if invitation.status != InvitationStatus.PENDING.value:  # type: ignore
            raise ValueError

        if invitation.expires_at <= now():
            raise ValueError

        invitation.status = InvitationStatus.ACCEPTED.value  # type: ignore
        invitation.save(update_fields=['status'])
        kwargs = {
            'invitation_id': invitation.id,
            'organization_id': invitation.organization.id,
            'permission_level': invitation.permission_level,
            'user_id': request_user.id,
        }
        member = self._member_model.objects.create(**kwargs)
        return member

    def decline_invitation(
        self: 'OrganizationService',
        *,
        invitation: Optional[BaseInvitation] = None,
        request_user: Optional[User] = None,
    ) -> BaseInvitation:
        if invitation is None or request_user is None:
            raise ValueError

        self._validate_instances(invitation=invitation, user=request_user)

        if invitation.status != InvitationStatus.PENDING.value:  # type: ignore
            raise ValueError

        invitation.status = InvitationStatus.DECLINED.value  # type: ignore
        invitation.save(update_fields=['status'])
        return invitation

    def revoke_expired_invitation_set(
        self: 'OrganizationService',
    ) -> DjangoQuerySet[BaseInvitation]:
        queryset = self._invitation_model.objects.all()
        queryset = queryset.filter(
            status=InvitationStatus.PENDING.value,  # type: ignore
        )
        queryset = queryset.filter(expires_at__lt=now())
        queryset.update(status=InvitationStatus.EXPIRED.value)  # type: ignore
        return queryset

    def get_member_set(
        self: 'OrganizationService',
        *,
        organization: Optional[BaseOrganization] = None,
        request_user: Optional[User] = None,
    ) -> DjangoQuerySet[BaseMember]:
        if organization is None and request_user is None:
            return self._member_model.objects.none()

        if organization is not None:
            self._validate_instances(organization=organization, user=request_user)
            self._check_user_permission(
                action='get_member_set',
                organization=organization,
                user=request_user,
            )
            queryset = self._member_model.objects.all()
            queryset = queryset.filter(organization_id=organization.id)

        else:
            self._validate_instances(user=request_user)
            queryset = self._member_model.objects.all()
            queryset = queryset.filter(user_id=request_user.id)

        queryset = queryset.select_related('invitation', 'organization', 'user')
        return queryset

    def get_member(
        self: 'OrganizationService',
        *,
        id: Optional[str] = None,
        organization: Optional[BaseOrganization] = None,
        request_user: Optional[User] = None,
        queryset: Optional[DjangoQuerySet[BaseMember]] = None,
    ) -> Optional[BaseMember]:
        if id is None or request_user is None:
            raise ValueError

        self._validate_instances(organization=organization, user=request_user, id=id)

        if queryset is not None:
            member_set = queryset

        elif organization is not None:
            member_set = self._member_model.objects.all()
            member_set = member_set.filter(organization_id=organization.id)

        else:
            member_set = self._member_model.objects.all()

        member_set = member_set.filter(id=UUID(id))
        member_set = member_set.select_related('invitation', 'organization', 'user')

        try:
            member = member_set.get()

        except ObjectDoesNotExist:
            return None

        else:
            self._check_user_permission(
                action='get_member',
                organization=organization or member.organization,
                user=request_user,
            )
            return member

    def create_owner(
        self: 'OrganizationService',
        *,
        organization: Optional[BaseOrganization] = None,
        user: Optional[User] = None,
    ) -> BaseMember:
        if organization is None or user is None or not user.is_authenticated:
            raise ValueError

        kwargs = {
            'organization_id': organization.id,
            'permission_level': PermissionLevel.OWNER.value,  # type: ignore
            'user_id': user.id,
        }
        member = self._member_model.objects.create(**kwargs)
        return member

    def update_member_permission(
        self: 'OrganizationService',
        *,
        member: Optional[BaseMember] = None,
        new_owner: Optional[User] = None,
        permission_level: Optional[int] = None,
        request_user: Optional[User] = None,
    ) -> BaseMember:
        if (
            member is None
            or permission_level is None
            or request_user is None
            or not isinstance(permission_level, int)
        ):
            raise ValueError

        self._validate_instances(member=member, user=request_user)

        if member.permission_level == permission_level:
            return member

        self._check_user_permission(
            action='update_member_permission',
            organization=member.organization,
            user=request_user,
        )

        if (
            member.permission_level == PermissionLevel.OWNER.value  # type: ignore
            and member.user_id == member.organization.owner_id
        ):
            if new_owner is None:
                raise ValueError

            self._validate_instances(user=new_owner)
            queryset = self._member_model.objects.all()
            queryset = queryset.filter(organization_id=member.organization_id)
            queryset = queryset.filter(user_id=new_owner.id)
            queryset = queryset.filter(
                permission_level=PermissionLevel.OWNER.value,  # type: ignore
            )

            if queryset.exists():
                member.organization.owner = new_owner
                member.organization.save(update_fields=['owner'])

            else:
                raise ValueError

        member.permission_level = permission_level
        member.save(update_fields=['permission_level'])
        return member
