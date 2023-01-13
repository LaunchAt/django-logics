from typing import Optional

from .models import Media


class MediaService:
    _media_model = Media

    def put(
        self: 'MediaService',
        *,
        external_url: Optional[str] = None,
        file: Optional[str] = None,
        file_location: str = '',
        file_name: str = '',
        media: Optional[Media] = None,
        title: Optional[str] = None,
    ) -> Media:
        has_external_url = external_url is not None
        has_file = file is not None

        if has_external_url and not has_file:
            if media is None:
                media = self._media_model()

            elif media.file:
                media.delete()
                media = self._media_model()

            if title is not None:
                media.title = title

            media.external_url = external_url
            media.file = None
            media.file_location = ''
            media.file_name = ''
            media.save()
            return media

        if not has_external_url and has_file:
            if media is None:
                media = self._media_model()

            elif media.file:
                media.delete()
                media = self._media_model()

            if title is not None:
                media.title = title

            media.external_url = ''
            media.file = file
            media.file_location = file_location
            media.file_name = file_name
            media.save()
            return media

        if not has_external_url and not has_file:
            if media is not None and title is not None:
                media.title = title
                media.save()
                return media

        raise ValueError
