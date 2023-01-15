from django.conf import settings
from django.http.response import HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_protect

from .models import MediaFile


@csrf_protect
def mediafile_upload_view(request):
    if request.FILES:
        mediafile = MediaFile.objects.create(
            file=request.FILES.get('file', None),
            file_location='uploads/',
        )
        return JsonResponse({'url': f'{settings.MEDIA_URL}{mediafile.file.name}'})

    else:
        return HttpResponseBadRequest()
