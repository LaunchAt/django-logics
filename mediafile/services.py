from uuid import UUID
from typing import Optional, TypeVar

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Model as DjangoModel

from .models import MediaFile

User = TypeVar('User', bound=DjangoModel)


class MediaFileService:
    _mediafile_model = MediaFile

    def get_mediafile(
        self: 'MediaFileService',
        *,
        id: Optional[str] = None,
        request_user: Optional[User] = None,
    ) -> Optional[MediaFile]:
        if id is None or request_user is None:
            raise ValueError

        queryset = self._mediafile_model.objects.all()
        queryset = queryset.filter(id=UUID(id))
        queryset = queryset.filter(owner_id=request_user.id)
        queryset = queryset.select_related('owner')

        try:
            return queryset.get()

        except ObjectDoesNotExist:
            return None

    def put(
        self: 'MediaFileService',
        *,
        external_url: Optional[str] = None,
        file: Optional[str] = None,
        file_location: str = '',
        file_name: str = '',
        mediafile: Optional[MediaFile] = None,
        title: Optional[str] = None,
        request_user: Optional[User] = None,
    ) -> MediaFile:
        has_external_url = external_url is not None
        has_file = file is not None

        if has_external_url and not has_file:
            if mediafile is None:
                mediafile = self._mediafile_model()

            elif mediafile.file:
                mediafile.delete()
                mediafile = self._mediafile_model()

            if title is not None:
                mediafile.title = title

            if request_user is not None:
                mediafile.owner_id = request_user.id

            mediafile.external_url = external_url
            mediafile.file = None
            mediafile.file_location = ''
            mediafile.file_name = ''
            mediafile.save()
            return mediafile

        if not has_external_url and has_file:
            if mediafile is None:
                mediafile = self._mediafile_model()

            elif mediafile.file:
                mediafile.delete()
                mediafile = self._mediafile_model()

            if title is not None:
                mediafile.title = title

            if request_user is not None:
                mediafile.owner_id = request_user.id

            mediafile.external_url = ''
            mediafile.file = file
            mediafile.file_location = file_location
            mediafile.file_name = file_name
            mediafile.save()
            return mediafile

        if not has_external_url and not has_file:
            if mediafile is not None and title is not None:
                mediafile.title = title
                mediafile.save()
                return mediafile

        raise ValueError
