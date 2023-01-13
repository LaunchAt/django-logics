from django.conf import settings
from django.http.response import HttpResponseBadRequest, JsonResponse
from django.views.decorators.csrf import csrf_protect

from .models import Media


@csrf_protect
def media_upload_view(request):
    if request.FILES:
        media = Media.objects.create(
            file=request.FILES.get('file', None),
            file_location='uploads/',
        )
        return JsonResponse({'location': f'{settings.MEDIA_URL}{media.file.name}'})

    else:
        return HttpResponseBadRequest()
